import queue
import threading
from tqdm.autonotebook import tqdm

from utils import *


class TestCaseMixin:

    def test_account_creation(self, num_worker_threads=32, pwr=5):
        self.create_accounts_parallel(pwr, num_worker_threads=num_worker_threads)
        err_dict = self.verify_account_creation(pwr)
        if len(err_dict):
            print(err_dict)
            return False
        return True

    def create_accounts_parallel(self, powr=6, num_worker_threads=8):
        r1_size = 30
        d_id = 0
        base_balance = 1000  # in milli-lgs
        send_amt = int(base_balance * (3 ** 10))
        print('Creating initial account group of {} accounts'.format(r1_size), end='')
        for i in range(r1_size):
            account = self.accounts[i]
            d_id, block_data = self.create_next_genesis_txn(account['account'], d_id, 2000000000000)
            self.nodes[d_id].process(block_data['block'])
            d_id = designated_delegate(g_pub, block_data['hash'])
            if not self.wait_for_blocks_persistence([block_data['hash']]):
                sys.stderr.write('Creation stopped at index {}, account {}'.format(i, account['account']))
                break
            print('.', end='')
        print()
        del d_id

        sender_size = r1_size

        for i in range(powr):
            print('\nStarting round i = {}'.format(i + 1))
            if not self.send_and_confirm(sender_size, send_amt, num_worker_threads):
                print('Failed at iteration with exponent i={}'.format(i))
                return
            send_amt = int(send_amt / 2)
            sender_size *= 2

    def verify_account_creation(self, powr=6):
        print('Verifying all accounts just got created...')
        err_dict = {}
        for i in tqdm(range(30 * (2 ** powr))):
            account = self.accounts[i]['account']
            try:
                self.update_account_frontier(account_addr=account)
            except LogosRPCError as e:
                err_dict[i] = e.__dict__
        return err_dict

    def update_account_frontier(self, account_addr):
        info = self.nodes[0].account_info(account_addr)
        self.account_frontiers[account_addr] = info['frontier']

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
        for j in range(sender_size):
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

        t1 = time()
        print('Time to process: {:.6f}s'.format(t1 - t0))
        blocks_to_check = [block_data['hash'] for block_data in block_data_list]
        if not self.wait_for_blocks_persistence(blocks_to_check):
            return False
        print('Time to wait for persistence: {:.6f}s'.format(time() - t1))
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
