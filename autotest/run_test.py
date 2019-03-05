import pickle
import re

from orchestration import *
import test_cases
from utils import *

WIDTH = 80


class TestRequests(*[getattr(test_cases, n).TestCaseMixin for n in test_cases.__all__]):
    """
    Cluster-agnostic test class
    """

    def __init__(self, cluster_arg, num_delegates=32):
        """

        Args:
            cluster_arg: (int or :obj:`str`) Either AWS Cloudformation cluster name, or integer indicating size of local cluster
            num_delegates: (int) ACTUAL size of the consensus group (can be smaller than num_nodes)
        """
        if isinstance(cluster_arg, str):
            self.remote = True
        elif isinstance(cluster_arg, int):
            self.remote = False
        else:
            raise RuntimeError('Unsupported cluster arg type')
        self.ips = (get_remote_cluster_ips if self.remote else get_local_cluster_ips)(cluster_arg)
        # reverse mapping of ip to global index
        self.ip_pub_to_i, self.ip_prv_to_i = {}, {}
        for k, v in self.ips.items():
            self.ip_pub_to_i[v['PublicIpAddress']] = k
            self.ip_prv_to_i[v['PrivateIpAddress']] = k
        if not self.ips:
            raise RuntimeError('Error retrieving IPs for cluster, does cluster exist?')
        self.log_handler = (RemoteLogsHandler if self.remote else LocalLogsHandler)(self.ips)
        self.nodes = {i: LogosRpc(ip['PublicIpAddress']) for i, ip in self.ips.items()}
        self.num_nodes = len(self.nodes)
        self.num_delegates = num_delegates
        self.reset_delegates()
        self.cluster = cluster_arg
        self.num_accounts = 60

        # Preload accounts, create if file not present
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data/accounts48000.pickle'), 'rb') as handle:
            self.accounts = pickle.load(handle)
            self.account_frontiers = {v['account']: {
                'frontier': '0' * 32,
                'i': k
            } for k, v in self.accounts.items()}  # easier lookup
            self.account_list = list(self.accounts.values())

        # Construct list of tests to rerun
        self.reruns = []
        for member_name in dir(self):
            if member_name.startswith('test_'):
                method = getattr(self, member_name)
                if hasattr(method, '__call__') and hasattr(method, 'rerun_needed') and not hasattr(method, 'to_skip'):
                    self.reruns.append(member_name)

    def run(self):
        num_test = 0
        num_passed = 0
        num_skipped = 0
        for member_name in dir(self):
            method = getattr(self, member_name)
            if member_name.startswith('test_') and member_name not in self.reruns and hasattr(method, '__call__'):
                num_test += 1
                if hasattr(method, 'to_skip'):
                    num_skipped += 1
                    print('Skipping {}'.format(to_test_name(member_name)))
                    continue
                TestRequests.print_test_name(to_test_name(member_name))

                # main test
                res = method()
                if not res:
                    print('Test failed!')
                    break

                # reruns
                for rerun_test_name in self.reruns:
                    print('\tRerunning {}'.format(to_test_name(rerun_test_name)))
                    res = getattr(self, rerun_test_name)()
                    if not res:
                        print('Test rerun failed!')
                        break
                if not res:
                    print('Test failed!')
                    break

                num_passed += 1
                print("Test succeeded.")
        print("=" * WIDTH)
        print('{}: {} of {} tests passed, {} skipped'.format(
            'SUCCESS' if num_test == (num_passed + num_skipped) else 'FAIL', num_passed, num_test, num_skipped))

    """
    Test cases
    """

    def test_dummy(self):
        print('DUMMY')
        return True

    """
    Helper functions
    """
    def restart_logos_p2p(self, clear_db=True):
        """
        Restarts logos_core in p2p mode on remote cluster

        Args:
            clear_db (bool): whether to wipe database on cluster

        Returns:
            list(:obj:`str`): list of command output from each node
        """
        files_to_rm = get_files_to_remove(clear_db)
        command_list = []
        for i, ip_dict in self.ips.items():
            command_line_options = '--bind {} --debug net '.format(ip_dict['PrivateIpAddress']) + \
                                   ' '.join(['--addnode {}'.format(
                                       self.ips[(i + inc) % self.num_nodes]['PublicIpAddress']
                                   ) for inc in [1, 4, 16]])
            command = '\n'.join([
                'sudo kill -9 $(pgrep logos_core)',
                'sudo rm -f {}'.format(files_to_rm),
                'sleep 20 && sudo ' + gen_start_logos_command(command_line_options),
            ])
            command_list.append(command)
        _ = self.log_handler.execute_parallel_command(command_list, background=True)
        # print('Succeeded on {} out of {} nodes'.format(sum(1 - bool(int(line)) for line in all_lines), self.num_nodes))
        # TODO: check if process actually runs
        self.reset_delegates()

    def reset_delegates(self):
        self.delegates = {i: self.nodes[i] for i in range(self.num_delegates)}  # delegates currently in office

    def is_cluster_initialized(self, from_all=False):
        if not self.is_cluster_running(None if from_all else 0, verbose=False):
            return False

        pattern = 'Received Post_Commit'
        if from_all:
            counts = self.log_handler.grep_count(pattern)
            print(counts[:self.num_delegates])
            return all(i == self.num_delegates - 1 for i in counts[:self.num_delegates])
        else:
            post_commit_count = self.log_handler.grep_count(pattern, 0)[0]
            if post_commit_count == self.num_delegates - 1:
                return True
            else:
                print('Received {} out of {} Post_Commit messages'.format(post_commit_count, self.num_delegates - 1))
                return False

    def is_cluster_running(self, node_id=None, verbose=True):
        pids = self.log_handler.collect_lines('pgrep logos_core', node_id)
        running = True
        for i, pid in enumerate(pids):
            if not pid:
                if verbose:
                    print('Node {} with ip {} is not running logos_core'.format(i, self.ips[i]))
                running = False
        err_lines = self.log_handler.grep_lines('(error|fatal)]', node_id)
        for i, err_line in enumerate(err_lines):
            if err_line:
                print('Node {} with ip {} reported the following error: {}\n'.format(i, self.ips[i], err_line))
                # running = False
        return running

    def get_stored_request_count(self, node_id=None):
        # TODO: change grep pattern once Devon code is merged, same as below
        all_lines = self.log_handler.collect_lines(
            'grep -r "Batch.*Stored" {}* | tail -n1'.format(self.log_handler.LOG_DIR),
            node_id
        )

        def stored_count_from_line(line):
            pat = 'ConsensusManager<BatchStateBlock> - Stored '
            m = re.search('{}([0-9]+)'.format(pat), line)
            return int(m.group(1)) if m is not None else 0

        return sum(stored_count_from_line(line) for line in all_lines)

    def get_stored_request_block_count(self, node_id=None):
        all_lines = self.log_handler.collect_lines(
            'grep -r "Batch.*Stored" {}* | wc -l'.format(self.log_handler.LOG_DIR),
            node_id
        )

        return sum(int(line) if line else 0 for line in all_lines)

    @staticmethod
    def print_test_name(name):
        length = len(name)
        print('=' * WIDTH)
        print('|' * WIDTH)
        print('|' * int((WIDTH - length) / 2) + name + '|' * int((WIDTH - length + 1) / 2))
        print('|' * WIDTH)

    def ip_prv_to_pub(self, prv_ip):
        return self.ips[self.ip_prv_to_i[prv_ip]]['PublicIpAddress']

    def del_id_to_node_id(self, del_id):
        return self.ip_pub_to_i[self.delegates[del_id].ip]

# TODO: regenerate delegate dict whenever epoch transition takes place


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print('Expected Usage:  python3 run_test.py <cluster_name>\n')
        sys.exit(0)
    elif len(sys.argv) == 1:
        cluster = 'InternalTest'
    else:
        cluster = sys.argv[1]
        
    if cluster is not 'InternalTest':
        restart_logos(cluster)
        
    test_case = TestRequests(cluster)
    while not test_case.is_cluster_initialized():
        sleep(2)
        
    test_case.run()
    
