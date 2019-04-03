from tqdm.autonotebook import tqdm

from utils import *

MAX_TXN = 8
PWR = 3
N_WORKERS = 32

class TestCaseMixin:

    def test_00_account_creation(self, pwr=PWR, txn_size=MAX_TXN, num_worker_threads=N_WORKERS):
        r1_size = int(self.num_accounts / 2)
        self.create_accounts_parallel(r1_size, pwr, txn_size, num_worker_threads=num_worker_threads)
        return self.verify_account_creation(r1_size, txn_size, pwr)

    def create_accounts_parallel(self, r1_size, powr=PWR, txn_size=MAX_TXN, num_worker_threads=N_WORKERS):
        d_id = 0
        base_balance = 1000  # in milli-lgs
        addn_mul = 3  # additional multiplier to provide leeway funding
        # additional + 1 for a very loose txn fee limit
        send_amt = int(base_balance * ((txn_size + 1 + 1) ** powr) * addn_mul)

        sender_size = r1_size * txn_size
        print('Creating initial account group of {} accounts'.format(sender_size), end='')
        for i in range(r1_size):
            txns = [{
                'destination': self.accounts[i * txn_size + j]['account'],
                'amount': send_amt
            } for j in range(txn_size)]
            d_id, request_data = self.create_next_genesis_txn(
                txns,
                d_id,
            )
            self.delegates[d_id].process(request_data['request'])
            d_id = designated_delegate(g_pub, request_data['hash'])
            if not self.wait_for_requests_persistence([request_data['hash']]):
                sys.stderr.write('Creation stopped at index {}, txns {}'.format(i, txns))
                break
            print('.', end='')
        print()
        del d_id

        for i in range(powr):
            print('\nStarting round i = {}'.format(i + 1))
            send_amt = int(send_amt / (txn_size + 1 + 1))
            if not self.send_and_confirm(sender_size, send_amt, txn_size, num_worker_threads):
                print('Failed at iteration with exponent i={}'.format(i))
                return
            sender_size *= (1 + txn_size)

    def verify_account_creation(self, r1_size, txn_size=MAX_TXN, powr=PWR):
        print('Verifying all accounts just got created...')
        num_to_check = (r1_size * txn_size) * ((txn_size + 1) ** powr)
        for account_slice in tqdm(batch(self.account_list[:num_to_check], 2000)):
            if self.delegates[0].accounts_exist([account['account'] for account in account_slice])['exist'] != '1':
                return False
        return True

    def update_account_frontier(self, account_addr):
        info = self.delegates[0].account_info(account_addr)
        self.account_frontiers[account_addr]['frontier'] = info['frontier']

    def send_and_confirm(self, sender_size, send_amt, txn_size=MAX_TXN, num_worker_threads=N_WORKERS):
        d_ids = [random.randrange(0, self.num_delegates) for _ in range(sender_size)]
        accounts_to_create = self.account_list[sender_size:sender_size * (1 + txn_size)]
        d_ids, request_data_list = zip(*[self.create_next_txn(
            self.accounts[j]['account'],
            self.accounts[j]['public'],
            self.accounts[j]['private'],
            [{
                'destination': accounts_to_create[j * txn_size + k]['account'],
                'amount': send_amt
            } for k in range(txn_size)],
            d_ids[j]
        ) for j in range(sender_size)])

        # construct queue
        q = Queue()
        # translate designated delegate ids into node ids
        d_ids = [self.del_id_to_node_id(d_id) for d_id in d_ids]

        for j in range(sender_size):
            q.put((j, d_ids[j], request_data_list[j]))
        resps = self.process_request_queue(q, num_worker_threads)
        for k, r in resps.items():
            if 'rpc_error' in r:
                print(k, r)

        t1 = time()
        requests_to_check = [request_data['hash'] for request_data in request_data_list]
        print('Time to construct check list: {:.6f}s'.format(time() - t1))
        if not self.wait_for_requests_persistence(requests_to_check):
            return False
        print('Time to wait for persistence: {:.6f}s'.format(time() - t1))
        return True

    def process_request_queue(self, q, num_worker_threads):
        """
        Parallel send requests to respective designated delegates to process

        Args:
            q (:obj:`Queue`): Queue containing 3-tuples of `(i, d_id, request_data)`, where
                `d_id` is the index of the *node* (not delegate!) to process the request and
                `request_data` is the request data returned by `self.create_next_txn`
            num_worker_threads (int): number of threads for parallel sending

        Returns:
            dict: dictionary mapping `{id: process_response}`
        """
        resps = {}

        # process worker thread
        def worker():
            while True:
                try:
                    j, d_id, request_data = q.get(block=False)
                except Empty:
                    break
                try:
                    resps[j] = self.nodes[d_id].process(request_data['request'])
                except LogosRPCError as e:
                    sys.stderr.write('Error at index {}!\n'.format(j))
                    resps[j] = e.__dict__
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
        return resps

    def create_next_txn(self, sender_addr, sender_pub, sender_prv, txns, designated_id=0):
        info_data = self.delegates[designated_id].account_info(sender_addr)
        prev = info_data['frontier']
        designated_id = designated_delegate(sender_pub, prev)
        for txn in txns:
            txn['amount'] = amount_mlgs_to_string(txn['amount'])
        create_data = self.delegates[designated_id].block_create(
            txns=txns,
            previous=prev,
            private_key=sender_prv,
            fee_mlgs=MIN_FEE_MLGS
        )
        return designated_id, create_data

    def create_next_genesis_txn(self, txns, designated_id=0):
        return self.create_next_txn(g_account, g_pub, g_prv, txns, designated_id)

    def wait_for_requests_persistence(self, hashes, max_batch=2000, max_retries=60):
        """
        Checks if given request hashes are persisted
        (This can be used to check if recipient accounts are created,
        assuming block persistence & account info update happen together)

        Args:
            hashes (list(:obj:`str`)): list of request hash strings to check
            max_batch (int): how many hashes should be queried in one RPC request
            max_retries (int): number of retries after which the check fails

        Returns:
            bool: whether all blocks are persisted
        """
        assert(all(LogosRpc.is_valid_hash(h) for h in hashes))

        def check_hash_persistence(hashes_to_check):
            # for i in range(self.num_nodes):
            for i in range(self.num_delegates):
                try:
                    exist = self.delegates[i].blocks_exist(hashes_to_check)
                except LogosRPCError:
                    return False
                assert exist['exist'] in ['0', '1']
                if exist['exist'] == '0':
                    return False
            return True

        retries = 0
        t0 = time()
        while True:
            if all(check_hash_persistence(txn_batch) for txn_batch in batch(hashes, max_batch)):
                return True
            sleep(1)
            retries += 1
            if retries > max_retries or time() - t0 > int(len(hashes) / 600 + 30):
                print(self.delegates[0].blocks(hashes))
                return False


def amount_mlgs_to_string(amount_mlgs):
    return str(amount_mlgs) + '0' * MLGS_DEC
