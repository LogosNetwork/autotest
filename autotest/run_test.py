import pickle
import re
from typing import List, Dict

from utils import *
from orchestration import *
import test_cases

WIDTH = 80


class TestRequests(*[getattr(test_cases, n).TestCaseMixin for n in test_cases.__all__]):
    """
    Cluster-agnostic test class
    """

    def __init__(self, cluster_arg, num_delegates=32, disable_transition=False):
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
        self.ips: Dict[int, Dict[str, str]] = \
            (get_remote_cluster_ips if self.remote else get_local_cluster_ips)(cluster_arg)
        if disable_transition:
            self.ips = {k: v for k, v in self.ips.items() if k < num_delegates}
        # reverse mapping of ip to global index
        self.ip_pub_to_i, self.ip_prv_to_i = {}, {}
        for k, v in self.ips.items():
            self.ip_pub_to_i[v['PublicIpAddress']] = k
            self.ip_prv_to_i[v['PrivateIpAddress']] = k
        if not self.ips:
            raise RuntimeError('Error retrieving IPs for cluster, does cluster exist?')
        self.log_handler = (RemoteLogsHandler if self.remote else LocalLogsHandler)(self.ips)
        self.nodes: Dict[int, LogosRpc] = {i: LogosRpc(ip['PublicIpAddress']) for i, ip in self.ips.items()}
        self.num_nodes: int = len(self.nodes)
        self.num_delegates: int = num_delegates
        self.reset_delegates()
        self.cluster = cluster_arg
        self.num_accounts: int = 6
        self.tokens = []
        
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
    def restart_logos_p2p(self, sleep=20, clear_db=True):
        """
        Restarts logos_core in p2p mode on remote cluster

        Args:
            sleep (int): sleep time before restarting software
            clear_db (bool): whether to wipe database on cluster

        Returns:
            list(:obj:`str`): list of command output from each node
        """
        files_to_rm = get_files_to_remove(clear_db)
        command_list = []
        for i, ip_dict in self.ips.items():

            # disable p2p and epoch transition if num nodes is the same as numdelegates
            if self.num_delegates == self.num_nodes:
                command_line_options = ''
            else:
                command_line_options = '--bind {} --debug net '.format(ip_dict['PrivateIpAddress']) + \
                                       ' '.join(['--addnode {}'.format(
                                           self.ips[(i + inc) % self.num_nodes]['PublicIpAddress']
                                       ) for inc in [1, 4, 16]])
            command = '\n'.join([
                'sudo kill -9 $(pgrep logos_core)',
                'sudo rm -f {}'.format(files_to_rm),
                'sleep {} && sudo '.format(sleep) + gen_start_logos_command(command_line_options),
            ])
            command_list.append(command)
        _ = self.log_handler.execute_parallel_command(command_list, background=True)
        self.reset_delegates()

    def bulk_sleeve(self, bls_prv_keys: List[str], ecies_prv_keys: List[str],
                    overwrite: bool = False) -> List[Dict[str, str]]:
        return [node.call('sleeve_store_keys', bls=bls_prv_keys[i], ecies=ecies_prv_keys[i], overwrite=overwrite)
                for i, node in self.nodes.items()]

    def bulk_activate(self):
        self.__bulk_call('delegate_activate')

    def __bulk_call(self, action: str, raise_error: bool = False, **kwargs):
        def thread_target(idx, **thread_kwargs):
            try:
                self.nodes[idx].call(action, **thread_kwargs)
            except LogosRPCError as err:
                if raise_error:
                    raise
                else:
                    print('Node {} - {}'.format(idx, err))
        threads = []
        for node_idx in range(self.num_nodes):
            t = threading.Thread(target=thread_target, args=(node_idx,), kwargs=kwargs)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def check_activation_status(self, check):
        for i in range(self.num_delegates):
            try:
                status = self.delegates[i].call('activation_status')
            except LogosRPCError:
                return False
            if status[check] == 'false':
                return False
        return True
            
    def reset_delegates(self):
        self.delegates = {i: self.nodes[i] for i in range(self.num_delegates)}  # delegates currently in office

    def is_cluster_initialized(self, from_all: bool = False):
        if not self.is_cluster_running(None if from_all else 0, verbose=0):
            return False

        # Check if each delegate's latest request block tip exists
        for idx in range(self.num_delegates):
            try:
                self.nodes[0].request_blocks_latest(delegate_id=idx, count=1)
            except LogosRPCError:
                return False
        return True

    def is_cluster_running(self, node_id: int = None, verbose: int = 0):
        pids = self.log_handler.collect_lines('pgrep logos_core', node_id)
        running = True
        for i, pid in enumerate(pids):
            if not pid:
                if verbose > 0:
                    print('Node {} with ip {} is not running logos_core'.format(i, self.ips[i]))
                running = False
        err_lines = self.log_handler.grep_lines('(error|fatal)]', node_id)
        for i, err_line in enumerate(err_lines):
            if err_line and verbose > 1:
                print('Node {} with ip {} reported the following error: {}\n'.format(i, self.ips[i], err_line))
                # running = False
        return running

    def get_stored_request_count(self, node_id=None):
        # TODO: change grep pattern once Devon code is merged, same as below
        all_lines = self.log_handler.collect_lines(
            'grep -r "Request.*Stored" {}* | tail -n1'.format(self.log_handler.LOG_DIR),
            node_id
        )

        def stored_count_from_line(line):
            pat = 'ConsensusManager<RequestBlock> - Stored '
            m = re.search('{}([0-9]+)'.format(pat), line)
            return int(m.group(1)) if m is not None else 0

        return sum(stored_count_from_line(line) for line in all_lines)

    def get_stored_request_block_count(self, node_id=None):
        all_lines = self.log_handler.collect_lines(
            'grep -r "Request.*Stored" {}* | wc -l'.format(self.log_handler.LOG_DIR),
            node_id
        )

        return sum(int(line) if line else 0 for line in all_lines)

    def get_respondents(self, node_id, block_hash, message_type='Prepare', direct=True):
        pattern = 'Received {}.* {} via direct connection {}'.format(
            message_type, block_hash, 'true' if direct else 'false'
        )
        lines = self.log_handler.grep_lines(pattern, node_id)[0].split('\n')
        return [int(re.search('from delegate: ([0-9]+)', line).group(1)) for line in lines]

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

    if cluster.isdigit():
        cluster = eval(cluster)

    if cluster is not 'InternalTest' and not isinstance(cluster, int):
        restart_logos(cluster)
        
    test_case = TestRequests(cluster)
    load = load_gov_keys()
    print("Loaded Keys")

    test_case.bulk_sleeve(load['BLS'], load['ECIES'])
    while not test_case.check_activation_status('sleeved'):
        sleep(2)
    print("Sleeved")
    
    test_case.bulk_activate()
    while not test_case.check_activation_status('activated'):
        sleep(2)
    print("Activated")
    
    while not test_case.is_cluster_initialized():
        sleep(2)

    test_case.run()
    #print(test_case.test_00_logos_req())
    #print(test_case.test_01_account_creation())
    #print(test_case.test_02_logos_req_illegal())
    #print(test_case.test_03_flood_receives())
    #print(test_case.test_10_token_req())
    #print(test_case.test_11_token_req_illegal())
    #print(test_case.test_12_token_req_flood())
