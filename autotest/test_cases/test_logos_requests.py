from utils import *
from orchestration import *
import random

class TestCaseMixin:

    def test_00_logos_requests(self):
        test_res = []
        #SEND TO GENESIS
        #test_res.append(self.genesis_to_self())
        
        #SEND TO ACCOUNT
        test_res.append(self.genesis_to_account())

        #SEND TO SELF
        #test_res.append(self.send_to_self())

        #SINGLE SEND PRIMARY
        test_res.append(self.single_send_primary())

        #SINGLE SEND BACKUP
        test_res.append(self.single_send_backup())

        return all(test_res)
                
    def test_02_flood_receives(self):
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
            [{
                'destination': dest_accounts[j]['account'],
                'amount': send_amt
            }],
            d_ids[j],
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

    def genesis_to_self(self):
        gen_before = self.nodes[0].account_info()
        gen_prev = gen_before['frontier']
        d_id = designated_delegate(g_pub, gen_prev)
        send_amt = 2**120
        created = self.nodes[d_id].block_create(
            previous=gen_prev,
            txns=[{"destination":g_account, "amount":send_amt}]
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at fund')
        gen_after = self.nodes[0].account_info()

        if eval(gen_after['balance']) != eval(gen_before['balance'])-eval(MIN_FEE):
            print("genesis to self: balance failed")
            return False
        return True

    def genesis_to_account(self):
        gen_before = self.nodes[0].account_info()
        gen_prev = gen_before['frontier']

        try:
            account_before = self.nodes[0].account_info(self.account_list[1]['account'])
            amount_before = eval(account_before['balance'])
        except LogosRPCError as error:
            amount_before = 0

        try:
            account2_before = self.nodes[0].account_info(self.account_list[2]['account'])
            amount2_before = eval(account2_before['balance'])
        except LogosRPCError as error:
            amount2_before = 0
        
        d_id = designated_delegate(g_pub, gen_prev)
        send_amt = eval(MIN_FEE)*5
        
        created = self.nodes[d_id].block_create(
            previous=gen_prev,
            txns=[{"destination":self.account_list[1]['account'], "amount":send_amt},
                  {"destination":self.account_list[2]['account'], "amount":send_amt+1}]
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Stopped at genesis_to_account')
            
        gen_after = self.nodes[0].account_info()
        account_after = self.nodes[0].account_info(self.account_list[1]['account'])
        account2_after = self.nodes[0].account_info(self.account_list[2]['account'])

        if eval(gen_after['balance']) != eval(gen_before['balance'])-send_amt-(send_amt+1)-eval(MIN_FEE):
            print("genesis to account: genesis balance failed")
            return False

        if eval(account_after['balance']) != send_amt + amount_before or eval(account2_after['balance']) != send_amt+1 + amount2_before:
            print("genesis to account: account balance failed")
            return False
        return True
        
    def send_to_self(self):
        account_before = self.nodes[0].account_info(self.account_list[1]['account'])
        account_prev = account_before['frontier']
        #print(account_before)
        d_id = designated_delegate(self.account_list[1]['public'], account_prev)

        send_amt=eval(account_before['balance'])/10
        created = self.nodes[d_id].block_create(
            private_key = self.account_list[1]['private'],
            previous=account_prev,
            txns=[{"destination":self.account_list[1]['account'], "amount":send_amt}]
        )
        #print(created)
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Stopped at send_to_self')

        account_after = self.nodes[0].account_info(self.account_list[1]['account'])
        
        if eval(account_after['balance']) != eval(account_before['balance'])-eval(MIN_FEE):
            print("send to self: account balance failed")
            return False
        return True
        
    def single_send_primary(self):
        account_before = self.nodes[0].account_info(self.account_list[1]['account'])
        account_prev = account_before['frontier']
        dest_before = self.nodes[0].account_info(self.account_list[2]['account'])
        d_id = designated_delegate(self.account_list[1]['public'], account_prev)

        send_amt=1234567890
        created = self.nodes[d_id].block_create(
            private_key = self.account_list[1]['private'],
            previous=account_prev,
            txns=[{"destination":self.account_list[2]['account'], "amount":send_amt}]
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Stopped at send_to_primary')

        account_after = self.nodes[0].account_info(self.account_list[1]['account'])
        dest_after = self.nodes[0].account_info(self.account_list[2]['account'])
        
        if eval(account_after['balance']) != eval(account_before['balance'])-send_amt-eval(MIN_FEE):
            print("single send primary: src balance failed {} = {} - {} - {}".format(account_after['balance'], account_before['balance'], send_amt, MIN_FEE))
            return False
        
            print("single send primary: dest balance failed")
            return False
        if eval(dest_after['balance']) != eval(dest_before['balance'])+send_amt:
            print("single send primary: dest balance failed")
            return False
        
    def single_send_backup(self):
        account_before = self.nodes[0].account_info(self.account_list[1]['account'])
        account_prev = account_before['frontier']
        dest_before = self.nodes[0].account_info(self.account_list[2]['account'])
        d_id = designated_delegate(self.account_list[1]['public'], account_prev)
        
        send_amt=2345678901
        created = self.nodes[d_id].block_create(
            private_key = self.account_list[1]['private'],
            previous=account_prev,
            txns=[{"destination":self.account_list[2]['account'], "amount":send_amt}]
        )
        self.nodes[d_id+1].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Stopped at send_to_primary')

        account_after = self.nodes[0].account_info(self.account_list[1]['account'])
        dest_after = self.nodes[0].account_info(self.account_list[2]['account'])
        
        if eval(account_after['balance']) != eval(account_before['balance'])-send_amt-eval(MIN_FEE):
            print("single send backup: src balance failed")
            return False
        if eval(dest_after['balance']) != eval(dest_before['balance'])+send_amt:
            print("single send backup: dest balance failed")
            return False
