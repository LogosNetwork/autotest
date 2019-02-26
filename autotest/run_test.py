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

        :param cluster_arg: Either AWS Cloudformation cluster name, or integer indicating size of local cluster
        :param num_delegates: ACTUAL size of the consensus group (can be smaller than num_nodes)
        """
        if isinstance(cluster_arg, str):
            self.remote = True
        elif isinstance(cluster_arg, int):
            self.remote = False
        else:
            raise RuntimeError('Unsupported cluster arg type')
        self.ips = (get_remote_cluster_ips if self.remote else get_local_cluster_ips)(cluster_arg)
        if not self.ips:
            raise RuntimeError('Error retrieving IPs for cluster, does cluster exist?')
        self.log_handler = (RemoteLogsHandler if self.remote else LocalLogsHandler)(self.ips)
        self.nodes = {i: LogosRpc(ip) for i, ip in self.ips.items()}
        self.num_nodes = len(self.nodes)
        self.num_delegates = num_delegates

        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data/accounts48000.pickle'), 'rb') as handle:
            self.accounts = pickle.load(handle)
            self.account_frontiers = {v['account']: '0' * 32 for v in self.accounts.values() }  # easier lookup
            self.account_list = list(self.accounts.values())

    def run(self):
        for member in dir(self):
            method = getattr(self, member)
            if member.startswith('test_') and hasattr(method, '__call__'):
                TestRequests.print_test_name(member.replace('_', ' ').upper())
                res = method()
                if not res:
                    print('Test failed! ')
                    break
                print("Test succeeded.")
        print("=" * WIDTH)
        print("All tests succeeded!")

    """
    Test cases
    """

    def test_epoch_creation(self):
        print('2')
        return True

    """
    Helper functions
    """

    def is_cluster_initialized(self, from_all=False):
        if not self.is_cluster_running(None if from_all else 0):
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
                running = True
        err_lines = self.log_handler.grep_lines('(error|fatal)]', node_id)
        for i, err_line in enumerate(err_lines):
            if err_line:
                print('Node {} with ip {} reported the following error: {}\n'.format(i, self.ips[i], err_line))
                running = True
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

    def designated_delegate_for_account(self, account_dict):  # note that this relies on a correct local frontiers
        return designated_delegate(account_dict['public'], self.account_frontiers[account_dict['account']])

    @staticmethod
    def print_test_name(name):
        length = len(name)
        print('=' * WIDTH)
        print('|' * WIDTH)
        print('|' * int((WIDTH - length) / 2) + name + '|' * int((WIDTH - length + 1) / 2))
        print('|' * WIDTH)

# TODO: regenerate delegate dict whenever epoch transition takes place


if __name__ == '__main__':
    test_case = TestRequests('InternalTest')
    test_case.test_account_creation()
