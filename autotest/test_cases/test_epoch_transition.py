from utils import *


class TestCaseMixin:

    def test_epoch_transition(self):
        timeout = 600
        # first tell delegates to start_epoch_transition, no delay
        for node in self.nodes.values():
            resp = node.call('start_epoch_transition')
            if 'result' not in resp or resp['result'] != 'in-progress':
                print(node.ip, resp, file=sys.stderr)

        # count occurrences of CONNECT|ETS|ES|ETE
        count_tmpl = 'grep -r "{{pat}}" {dir}* | wc -l'.format(dir=RemoteLogsHandler.LOG_DIR)
        command = '\n'.join(count_tmpl.format(pat=pat) for pat in [
            'ConsensusContainer::EpochTransitionEventsStart',
            'ConsensusContainer::EpochTransitionStart',
            'ConsensusContainer::EpochStart',
            'ConsensusContainer::EpochTransitionEnd',
        ])
        t0 = time()
        counter = 0
        while True:
            count_strings = self.log_handler.collect_lines(command)
            counts = [[int(s) for s in line.rstrip('\n').split('\n')] for line in count_strings]
            counts = [sum(zipped) for zipped in zip(*counts)]
            print(' ' * 60, end='\r')
            print('|| Connect: {:2} | ETS: {:2} | ES: {:2} | ETE: {:2} || {}'.format(*counts, '.' * counter), end='\r')
            if counts == [64, 40, 40, 40]:
                print('\nCount matched')
                return True
            if time() - t0 > timeout:
                return False
            counter = counter % 3 + 1
            sleep(5)

        # then test sending transactions to different delegate groups
        # 1. retiring

        # 2. persistent

        # 3. new

        # TODO: test delay scenario
        pass
