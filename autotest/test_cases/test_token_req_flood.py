from utils import *
from orchestration import *
import random
import qlmdb3
import math

MAX_TXN = 8
PWR = 1
N_WORKERS = 32

class TestCaseMixin:

    def test_12_token_req_flood(self, num_worker_threads=N_WORKERS, pwr=PWR):
        return self.create_tokens_parallel(int(self.num_accounts/2), pwr, num_worker_threads=num_worker_threads)

    def create_tokens_parallel(self, r1_size, powr=PWR, txn_size=MAX_TXN, num_worker_threads=N_WORKERS):
        d_id = 0
        fund_amt = 2345678901234567890123456789
        total_supply = 2100000000000000
        print('Creating initial token group of {} tokens'.format(r1_size), end='')
        gen_prev = self.nodes[0].account_info()['frontier']
        for i in range(r1_size):
            #print("start creation")
            account = self.accounts[i]
            d_id, request_data, tok_account, tok_id = self.create_issuance(account, total_supply, d_id, i)
            self.delegates[d_id].process(request_data['request'])
            ##d_id = designated_delegate(g_pub, request_data['hash'])
            if not self.wait_for_requests_persistence([request_data['hash']]):
                sys.stderr.write('Creation stopped at index {}, account {}'.format(i, account['account']))
                break
            self.tokens.append({"id":tok_id, "account":tok_account})
            print('.', end='')
            
            d_id = designated_delegate(g_pub, gen_prev)
            created = self.nodes[d_id].block_create(
                previous=gen_prev,
                txns=[{"destination":tok_account, "amount":fund_amt}]
            )
            
            self.nodes[d_id].process(created['request'])
            if not self.wait_for_requests_persistence([created['hash']]):
                sys.stderr.write('Creation stopped at funding index {}, account {}'.format(i, tok_account))
            gen_prev = created['hash']
            
        print()
        del d_id

        #print(self.tokens)
        send_amt = int(total_supply/10000)
        if not self.distribute_and_confirm(r1_size, send_amt, num_worker_threads):
                print('Failed at iteration with exponent i={}'.format(i))
                return False
        sender_size = r1_size
        for i in range(powr):
            print('\nStarting round i = {} of {} txns'.format(i + 1, sender_size*8))
            send_amt = int(send_amt / (txn_size + 1 + 1))
            if not self.send_token_and_confirm(sender_size, send_amt, self.tokens[0]['id'], txn_size, num_worker_threads):
                print('Failed at iteration with exponent i={}'.format(i))
                return False
            sender_size *= (1 + txn_size)

        return True
    
    def create_issuance(self, account, supply, designated_id=0, symbol=0):
        info_data = self.nodes[designated_id].account_info(account['account'])
        prev = info_data['frontier']
        designated_id = designated_delegate(account['public'], prev)
        create_data = self.nodes[designated_id].block_create_issuance(
            private_key=account['private'],
            previous=prev,
            total_supply=supply,
            symbol='TOK'+str(symbol),
            name='test_token-'+str(symbol),
            controllers=[{"account":account['account'], "privileges": ["distribute", "burn", "issuance", "withdraw_fee", "withdraw_logos", "revoke", "update_issuer_info"]}],
            settings=["revoke", "issuance"],
            fee=MIN_FEE
        )
        coin = eval(create_data['request'])
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        token_id = coin['token_id']
        return designated_id, create_data, token_account, token_id
        

    def distribute_and_confirm(self, sender_size, send_amt, num_worker_threads):
        d_ids = [random.randrange(0, self.num_delegates) for _ in range(sender_size)]
        accounts_to_dist = self.account_list[0:sender_size*2]

        ##print(sender_size)

        for i in range(sender_size):
            #print(i)
            requests_to_check = []
            for j in range(sender_size):
                d_id, create_data = self.create_distribute(
                    self.account_list[j],
                    self.tokens[j],
                    accounts_to_dist[i]['account'],
                    send_amt,
                    d_ids[j]
                )

                self.nodes[d_id].process(create_data['request'])
                requests_to_check.append(create_data['hash'])
            if not self.wait_for_requests_persistence(requests_to_check):
                return False
        return True
        
    def create_distribute(self, account, token, dest, amt, designated_id=0):
        info_data = self.nodes[designated_id].account_info(token['account'])
        prev = info_data['frontier']
        designated_id = designated_delegate(account['public'], prev)
        create_data = self.nodes[designated_id].block_create_distribute(
            type="distribute",
            private_key=account['private'],
            previous=prev,
            token_id=token['id'],
            transaction={"destination":dest, "amount":amt},
            fee=MIN_FEE
        )
        return designated_id, create_data

    def send_token_and_confirm(self, sender_size, send_amt, token_id, txn_size=MAX_TXN, num_worker_threads=N_WORKERS):
        d_ids = [random.randrange(0, self.num_delegates) for _ in range(sender_size)]
        accounts_to_create = self.account_list[sender_size:sender_size * (1 + txn_size)]
        d_ids, request_data_list = zip(*[self.create_next_token_txn(
            self.accounts[j]['account'],
            self.accounts[j]['public'],
            self.accounts[j]['private'],
            [{
                'destination': accounts_to_create[j * txn_size + k]['account'],
                'amount': send_amt
            } for k in range(txn_size)],
            token_id,
            d_ids[j]
        ) for j in range(sender_size)])

        # construct queue
        q = Queue()
        # translate designated delegate ids into node ids
        d_ids = [self.del_id_to_node_id(d_id) for d_id in d_ids]

        for j in range(sender_size):
            q.put((j, d_ids[j], request_data_list[j]))
        #print(request_data_list)
        #print(q.qsize())
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

    
    def create_next_token_txn(self, sender_addr, sender_pub, sender_prv, txns, token_id, designated_id=0):
        info_data = self.delegates[designated_id].account_info(sender_addr)
        prev = info_data['frontier']
        designated_id = designated_delegate(sender_pub, prev)
        #for txn in txns:
        #    txn['amount'] = amount_mlgs_to_string(txn['amount'])
        create_data = self.delegates[designated_id].block_create_token_send(
            transactions=txns,
            token_id=token_id,
            previous=prev,
            token_fee=0,
            private_key=sender_prv,
            fee=MIN_FEE
        )
        return designated_id, create_data

    def wait_for_requests_persistence_sgu(self, hashes, max_batch=2000, max_retries=60):
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
                    #print(i)
                    #print(hashes_to_check)
                    #print(exist)
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
