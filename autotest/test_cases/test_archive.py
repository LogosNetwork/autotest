from utils import *
from orchestration import *

class TestCaseMixin:
    @skip
    def test_06_micro_archive(self):
        #for node in self.nodes.values():
        #    res = node.microblock_test()

        del_id = 0        
        res = self.nodes[del_id].microblock_test()

        primary_str = self.log_handler.grep_lines('ConsensusManager<MicroBlock>::OnDelegateMessage', del_id)[0]
        print(primary_str)
        last_micro = primary_str.split('\n')[-1]
        print("LAS")
        print(last_micro)
        mb_hash = last_micro.split('- hash: ')[1]
        print(mb_hash)
        timeout = 60
        t0 = time()

        while True:
            print('loop')
            #print(mb_hash)
            #commits = self.log_handler.grep_lines('ConsensusConnection<MicroBlock> - Received Commit message from delegate:', del_id)[0]
            commits = self.log_handler.grep_lines('DelegateBridge<MicroBlock> - Received Commit message from delegate:', del_id)[0]
            count = 0
            #print(commits)
            # if self.remote:
            for com in commits.split('\n'):
                print(com)
                print(com.split('with block hash '))
                if com.split('with block hash ')[1] == mb_hash + ' via direct connection true':
                    count += 1
            #else:
            #    for com in commits:
            #        print(com)
            #        print(com.split('with block hash '))
            #        if com.split('with block hash ')[1] == mb_hash + ' via direct connection true':
            #            count += 1
            print(count)
            print(self.num_delegates)
            if count == self.num_delegates-1:
                break
            if time() - t0 > timeout:
                print('\nTimed out!')
                return False
            print('sleep')
            print(mb_hash)
            print(del_id)
            sleep(2)
        
        run_db_get(self.cluster, 'micro_block_db', mb_hash, remote=self.remote)
        try:
            db_res = self.log_handler.grep_count('micro_block_db find: {} found'.format(mb_hash), 0)
        except:
            return False
        if db_res.count(1) == self.num_delegates:
            return True
        print(db_res)
        return False

    
