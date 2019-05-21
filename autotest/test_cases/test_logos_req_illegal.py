from utils import *

class TestCaseMixin:

    def test_02_logos_req_illegal(self, sender_size=10, num_worker_threads=8):
        d_ids = [random.randrange(0, self.num_delegates) for _ in range(sender_size)]
        errors = 0
        tests = 0
        
        for j in range(sender_size):
            info = self.nodes[0].account_info(self.accounts[j]['account'])
            invalid_amt = random.choice([(int(info['balance']) + random.randrange(1, 10)),
                                         -random.randrange(1, int(info['balance']))])
            try:
                tests += 1
                did, block = self.create_next_txn(
                    self.accounts[j]['account'],
                    self.accounts[j]['public'],
                    self.accounts[j]['private'],
                    [{
                        'destination': self.accounts[random.randrange(0, sender_size)],
                        'amount': invalid_amt
                    }],
                    d_ids[j],
                )
            except LogosRPCError:
                errors += 1
                continue

        if errors == tests:    
            return True
        
        return False
