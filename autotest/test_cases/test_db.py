from tqdm.autonotebook import tqdm
import re
from orchestration import *
from utils import *

class TestCaseMixin:

    def test_db(self):
        res = run_db_test(self.cluster)
        for i in range(len(self.nodes)):
            print('db checker on node{}'.format(i))
            line = self.log_handler.grep_lines('DATABASE CHECKER', i)[0]
            if not line:
                continue
            else:
                line = line.split('\n')[-1]
                [run, error, fail] = re.findall(r'\d+', line)
                if fail != '0' or error != '0':
                    return False
        return True
