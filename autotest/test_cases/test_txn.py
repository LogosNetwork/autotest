from utils import *
from orchestration import *
import random

class TestCaseMixin:

    def test_01_single_txn_primary(self):
        src_accounts =  [self.account_list[random.randint(0,self.num_accounts-1)]]
        dest_accounts = [self.account_list[random.randint(0,self.num_accounts-1)]]
        return self.send_and_confirm_txn(1, 100, src_accounts, dest_accounts, 1)

    def test_02_single_txn_backup(self):
        src_accounts =  [self.account_list[random.randint(0,self.num_accounts-1)]]
        dest_accounts = [self.account_list[random.randint(0,self.num_accounts-1)]]
        return self.send_and_confirm_txn(1, 100, src_accounts, dest_accounts, 1, backup=True)

    def test_03_send_to_self(self):
        src_accounts =  [self.account_list[random.randint(0,self.num_accounts-1)]]
        return self.send_and_confirm_txn(1, 100, src_accounts, src_accounts, 1)
        
    def test_04_flood_receives(self):
        src_accounts = self.account_list[0:self.num_accounts]      
        dest_accounts = [self.account_list[random.randint(0,self.num_accounts-1)]]*self.num_accounts
        return self.send_and_confirm_txn(self.num_accounts, 100, src_accounts, dest_accounts, 8)
        
    def send_and_confirm_txn(self, sender_size, send_amt, src_accounts, dest_accounts, num_worker_threads, backup=False):
        d_ids = [random.randrange(0, self.num_delegates) for _ in range(sender_size)]
        #dest_accounts = self.account_list[0:self.num_accounts-1]
        #random.shuffle(dest_accounts, random.random)
        #print(sender_size)
        #print(len(src_accounts))
        #print(len(dest_accounts))
        
        d_ids, request_data_list = zip(*[self.create_next_txn(
            src_accounts[j]['account'],
            src_accounts[j]['public'],
            src_accounts[j]['private'],
            dest_accounts[j]['account'],
            d_ids[j],
            send_amt
        ) for j in range(sender_size)])

        # construct queue
        q = Queue()
        if backup:
            d_ids = tuple(x+1 for x in d_ids)
        d_ids = [self.del_id_to_node_id(d_id) for d_id in d_ids]
        for j in range(sender_size):
            q.put((j, d_ids[j], request_data_list[j]))
        _ = self.process_request_queue(q, num_worker_threads)

        t1 = time()
        requests_to_check = [request_data['hash'] for request_data in request_data_list]
        if not self.wait_for_requests_persistence(requests_to_check):
            return False
        print('Time to wait for persistence: {:.6f}s'.format(time() - t1))
        return True
