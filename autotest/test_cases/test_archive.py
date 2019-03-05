from utils import *
from orchestration import *

class TestCaseMixin:
    
    def test_06_micro_archive(self):
        #for node in self.nodes.values():
        #    res = node.microblock_test()

        del_id = 0        
        res = self.nodes[del_id].microblock_test()

        primary_str = self.log_handler.grep_lines('ConsensusManager<MicroBlock>::OnSendRequest', del_id)[0]

        last_micro = primary_str.split('\n')[-1]
        mb_hash = last_micro.split('- hash: ')[1]

        timeout = 600
        t0 = time()

        while True:
            commits = self.log_handler.grep_lines('ConsensusConnection<MicroBlock> - Received Commit message from delegate:', del_id)[0]

            count = 0
            for com in commits.split('\n'):
                if com.split('with block hash ')[1] == mb_hash:
                    count += 1
            if count == self.num_delegates-1:
                break
            if time() - t0 > timeout:
                print('\nTimed out!')
                return False
            sleep(2)
        
        run_db_get(self.cluster, 'micro_block_db', mb_hash)
        db_res = self.log_handler.grep_count('micro_block_db find: {} found'.format(mb_hash))

        if db_res.count(1) == self.num_delegates:
            return True
        print(db_res)
        return False

    
