import re
from orchestration import *
from utils import *


class TestCaseMixin:

    @skip
    # @rerun_needed
    def test_db(self):
        _ = run_db_test(self.cluster)
        for i in range(len(self.nodes)):
            print('db checker on node{}'.format(i))
            line = self.log_handler.grep_lines('DATABASE CHECKER', i)[0]
            if not line:
                continue
            else:
                line = line.split('\n')[-1]
                _, error, fail = re.findall(r'\d+', line)
                if fail != '0' or error != '0':
                    return False
        return True
