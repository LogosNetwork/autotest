import pickle
import queue
import re
import threading
from time import sleep, time

from orchestration import *
from utils import *


class TestRequests:
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
            self.account_list = list(self.accounts.values())

    def run(self):
        for member in dir(self):
            method = getattr(self, member)
            if member.startswith('test_') and hasattr(method, '__call__'):
                print(member.replace('_', ' '))
                method()

    """
    Test cases
    """

    def test_account_creation(self, num_worker_threads=32, pwr=5):
        self.create_accounts_parallel(pwr, num_worker_threads=num_worker_threads)
        err_dict = self.verify_account_creation(pwr)
        if len(err_dict):
            print(err_dict)
            return False
        return True

    """
    Helper functions
    """

    def is_cluster_initialized(self, from_all=False):
        pattern = 'Received Post_Commit'
        if from_all:
            counts = self.log_handler.grep_count(pattern)
            for i in range(self.num_nodes):
                print('Node {} count: {}'.format(i, counts[i]))
            return all(i == self.num_delegates - 1 for i in counts)
        else:
            post_commit_count = self.log_handler.grep_count(pattern, 0)[0]
            if post_commit_count == self.num_delegates - 1:
                return True
            else:
                print('Received {} out of {} Post_Commit messages'.format(post_commit_count, self.num_delegates - 1))
                return False

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

        return sum(int(line.rstrip('\n')) if line else 0 for line in all_lines)

    def create_accounts_parallel(self, powr=6, num_worker_threads=8):
        r1_size = 30
        d_id = 0
        base_balance = 1000  # in milli-lgs
        send_amt = int(base_balance * (3 ** 10))
        for i in tqdm(range(r1_size)):
            account = self.accounts[i]
            d_id, block_data = self.create_next_genesis_txn(account['account'], d_id, 2000000000000)
            self.nodes[d_id].process(block_data['block'])
            d_id = designated_delegate(g_pub, block_data['hash'])
            if not self.wait_for_blocks_persistence([block_data['hash']]):
                sys.stderr.write('Creation stopped at index {}, account {}'.format(i, account['account']))
                break
        del d_id

        sender_size = r1_size

        for i in range(powr):
            print('Starting round i = {}'.format(i + 1))
            t0 = time()
            if not self.send_and_confirm(sender_size, send_amt, num_worker_threads):
                print('Failed at iteration with exponent i={}'.format(i))
                return
            send_amt = int(send_amt / 2)
            sender_size *= 2
            print('Finished in {}s'.format(time() - t0))

    def verify_account_creation(self, powr=6):
        err_dict = {}
        for i in tqdm(range(30 * (2 ** powr))):
            account = self.accounts[i]['account']
            try:
                self.nodes[0].account_info(account)
            except LogosRPCError as e:
                err_dict[i] = e.__dict__
        return err_dict

    def send_and_confirm(self, sender_size, send_amt, num_worker_threads):
        d_ids = [random.randrange(0, self.num_delegates) for _ in range(sender_size)]
        accounts_to_create = self.account_list[sender_size:sender_size * 2]
        d_ids, block_data_list = zip(*[self.create_next_txn(
            self.accounts[j]['account'],
            self.accounts[j]['public'],
            self.accounts[j]['private'],
            accounts_to_create[j]['account'],
            d_ids[j],
            send_amt
        ) for j in range(sender_size)])
        resps = {}

        # construct queue
        q = queue.Queue()
        for j in tqdm(range(sender_size)):
            q.put((j, d_ids[j], block_data_list[j]))

        # process worker thread
        def worker():
            while True:
                try:
                    j, d_id, block_data = q.get(block=False)
                except queue.Empty:
                    break
                try:
                    resps[j] = self.nodes[d_ids[j]].process(block_data_list[j]['block'])
                except LogosRPCError:
                    sys.stderr.write('Error at index {}!\n'.format(j))
                    raise
                q.task_done()

        t0 = time()
        # try to process every request
        threads = []
        for i in range(num_worker_threads):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        # block until all tasks are done
        q.join()
        # stop workers
        for t in threads:
            t.join()

        print('Time to process: {}'.format(time() - t0))
        blocks_to_check = [block_data['hash'] for block_data in block_data_list]
        if not self.wait_for_blocks_persistence(blocks_to_check):
            return False
        return True

    def create_next_txn(self, sender_addr, sender_pub, sender_prv, destination, designated_id=0, amount_mlgs=None):
        info_data = self.nodes[designated_id].account_info(sender_addr)
        prev = info_data['frontier']
        designated_id = designated_delegate(sender_pub, prev)
        if amount_mlgs is None:
            amount_mlgs = designated_id + 1
        assert isinstance(amount_mlgs, int)
        amount = str(amount_mlgs) + '0' * MLGS_DEC
        create_data = self.nodes[designated_id].block_create(
            amount=amount,
            destination=destination,
            previous=prev,
            key=sender_prv,
            fee_mlgs=MIN_FEE_MLGS
        )
        return designated_id, create_data

    def create_next_genesis_txn(self, destination, designated_id=0, amount_mlgs=None):
        return self.create_next_txn(g_account, g_pub, g_prv, destination, designated_id, amount_mlgs)

    # This assumes block persistence & account info update happen together
    def wait_for_blocks_persistence(self, txn_hashes, max_batch=2000):
        assert(all(LogosRpc.is_valid_hash(h) for h in txn_hashes))

        def batch(iterable, n=1):
            length = len(iterable)
            for idx in range(0, length, n):
                yield iterable[idx:min(idx + n, length)]

        def check_hash_persistence(hashes_to_check):
            # for i in range(self.num_nodes):
            for i in range(self.num_delegates):
                try:
                    self.nodes[i].blocks(hashes_to_check)
                except LogosRPCError:
                    return False
            return True

        max_retries = 30
        retries = 0
        t0 = time()
        while True:
            if all(check_hash_persistence(txn_batch) for txn_batch in batch(txn_hashes, max_batch)):
                return True
            sleep(1)
            retries += 1
            if retries > max_retries and time() - t0 > 300:
                print(self.nodes[0].blocks(txn_hashes))
                return False

# TODO: regenerate delegate dict whenever epoch transition takes place


if __name__ == '__main__':
    test_case = TestRequests('InternalTest')
    test_case.test_account_creation()
