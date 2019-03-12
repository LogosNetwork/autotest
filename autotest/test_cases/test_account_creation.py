from tqdm.autonotebook import tqdm

from utils import *


class TestCaseMixin:

    def test_00_account_creation(self, num_worker_threads=32, pwr=5):
        self.create_accounts_parallel(int(self.num_accounts/2), pwr, num_worker_threads=num_worker_threads)
        err_dict = self.verify_account_creation(pwr)
        if len(err_dict):
            print(err_dict)
            return False
        return True

    def create_accounts_parallel(self, r1_size, powr=5, num_worker_threads=8):
        d_id = 0
        base_balance = 1000  # in milli-lgs
        send_amt = int(base_balance * (3 ** 10))
        print('Creating initial account group of {} accounts'.format(r1_size), end='')
        for i in range(r1_size):
            account = self.accounts[i]
            d_id, request_data = self.create_next_genesis_txn(account['account'], d_id, 2000000000000)
            self.delegates[d_id].process(request_data['block'])
            d_id = designated_delegate(g_pub, request_data['hash'])
            if not self.wait_for_requests_persistence([request_data['hash']]):
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

    def verify_account_creation(self, powr=5):
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
        info = self.delegates[0].account_info(account_addr)
        self.account_frontiers[account_addr]['frontier'] = info['frontier']

    def send_and_confirm(self, sender_size, send_amt, num_worker_threads):
        d_ids = [random.randrange(0, self.num_delegates) for _ in range(sender_size)]
        accounts_to_create = self.account_list[sender_size:sender_size * 2]
        d_ids, request_data_list = zip(*[self.create_next_txn(
            self.accounts[j]['account'],
            self.accounts[j]['public'],
            self.accounts[j]['private'],
            accounts_to_create[j]['account'],
            d_ids[j],
            send_amt
        ) for j in range(sender_size)])

        # construct queue
        q = Queue()
        # translate designated delegate ids into node ids
        d_ids = [self.del_id_to_node_id(d_id) for d_id in d_ids]

        for j in range(sender_size):
            q.put((j, d_ids[j], request_data_list[j]))
        resps = self.process_request_queue(q, num_worker_threads)
        if resps:
            print(resps)

        t1 = time()
        requests_to_check = [request_data['hash'] for request_data in request_data_list]
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
                    resps[j] = self.nodes[d_id].process(request_data['block'])
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

    def create_next_txn(self, sender_addr, sender_pub, sender_prv, destination, designated_id=0, amount_mlgs=None):
        info_data = self.delegates[designated_id].account_info(sender_addr)
        prev = info_data['frontier']
        designated_id = designated_delegate(sender_pub, prev)
        if amount_mlgs is None:
            amount_mlgs = designated_id + 1
        assert isinstance(amount_mlgs, int)
        amount = str(amount_mlgs) + '0' * MLGS_DEC
        create_data = self.delegates[designated_id].block_create(
            amount=amount,
            destination=destination,
            previous=prev,
            key=sender_prv,
            fee_mlgs=MIN_FEE_MLGS
        )
        return designated_id, create_data

    def create_next_genesis_txn(self, destination, designated_id=0, amount_mlgs=None):
        return self.create_next_txn(g_account, g_pub, g_prv, destination, designated_id, amount_mlgs)

    def wait_for_requests_persistence(self, hashes, max_batch=2000, max_retries=30):
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
                    self.delegates[i].blocks(hashes_to_check)
                except LogosRPCError:
                    return False
            return True

        retries = 0
        t0 = time()
        while True:
            if all(check_hash_persistence(txn_batch) for txn_batch in batch(hashes, max_batch)):
                return True
            sleep(1)
            retries += 1
            if retries > max_retries or time() - t0 > 30:
                print(self.delegates[0].blocks(hashes))
                return False
