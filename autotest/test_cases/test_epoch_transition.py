from enum import Enum, auto
from random import choice
from utils import *


class EpochEvents(Enum):
    Con = auto()
    ETS = auto()
    ES = auto()
    ETE = auto()


class DelegateTypes(Enum):
    RETIRING = auto()
    PERSISTENT = auto()
    NEW = auto()


class TestCaseMixin:

    def test_07_epoch_transition(self, num_worker_threads=32):
        """
        Signals the cluster to start epoch transition, then listens to epoch events [connect (C)|transition start (ETS)|
        epoch start (ES)|transition end(ETE)] and at each event occurrence send one transaction to a delegate from
        each group of [retiring|persistent|new] delegates

        Correct behavior for accepting txns is:

        +-----+----------------------+----------+---+
        |Event|Retiring              |Persistent|New|
        +=====+======================+==========+===+
        | C   | yes                  |   yes    |no |
        +-----+----------------------+----------+---+
        | ETS | yes                  |   yes    |yes|
        |     | (might not complete) |          |   |
        +-----+----------------------+----------+---+
        | ES  | no                   |   yes    |yes|
        +-----+----------------------+----------+---+
        | ETE | no                   |   yes    |yes|
        +-----+----------------------+----------+---+


        Returns:
            bool: whether test passes

        """
        if self.num_nodes != self.num_delegates * 2:  # cluster size doesn't support epoch transition test
            print('Skipping test. Num nodes {} num delegates'.format(self.num_nodes, self.num_delegates))
            return True

        # Matches doc string above
        event_del_accept = [
            [1, 1, 0],
            [1, 1, 1],
            [0, 1, 1],
            [0, 1, 1],
        ]

        # construct new delegate mappings
        # get delegates for current and next epoch (convert from private IPs first)
        cur_dels = {int(k): self.ip_prv_to_pub(v['ip']) for k, v in self.delegates[0].epoch_delegates_current().items()}
        next_dels = {int(k): self.ip_prv_to_pub(v['ip']) for k, v in self.delegates[0].epoch_delegates_next().items()}
        new_delegate_nodes = {k: self.nodes[self.ip_pub_to_i[v]] for k, v in next_dels.items()}
        # essentially a two-way dictionary for easier lookup
        cur_dels_two_way = {k: v for k0, v0 in cur_dels.items() for k, v in ((k0, v0), (v0, k0))}
        next_dels_two_way = {k: v for k0, v0 in next_dels.items() for k, v in ((k0, v0), (v0, k0))}
        cur_set, next_set = set(v for v in cur_dels.values()), set(v for v in next_dels.values())
        persistent_set = cur_set.intersection(next_set)
        old_dels = {cur_dels_two_way[ip]: ip for ip in (cur_set - next_set)}
        new_dels = {next_dels_two_way[ip]: ip for ip in (next_set - cur_set)}
        persistent_dels_old = {cur_dels_two_way[ip]: ip for ip in persistent_set}
        persistent_dels_new = {next_dels_two_way[ip]: ip for ip in persistent_set}
        print(old_dels)
        print(new_dels)
        print(persistent_dels_old)
        print(persistent_dels_new)

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
        n_overlap = int(self.num_delegates * 5 / 4)
        desired_counts = {i: v for i, v in enumerate([self.num_nodes, n_overlap, n_overlap, n_overlap])}

        t0 = time()
        counter = 0
        while True:
            count_strings = self.log_handler.collect_lines(command)
            counts = [[int(s) for s in line.rstrip('\n').split('\n')] for line in count_strings]
            counts = [sum(zipped) for zipped in zip(*counts)]
            print(' ' * 60, end='\r')
            print('|| Connect: {:2} | ETS: {:2} | ES: {:2} | ETE: {:2} || {}'.format(*counts, '.' * counter), end='\r')
            # Check for each event
            for i, count in enumerate(counts):
                if i not in desired_counts:  # event already took place
                    continue
                if count == desired_counts[i]:  # event just took place
                    print('\n')
                    if i == 2:
                        self.delegates = new_delegate_nodes  # change delegates in office
                    # send transactions
                    q = Queue()
                    d_ids = [
                        choice(list(old_dels.keys())),  # retiring
                        choice(list((persistent_dels_old if i < 2 else persistent_dels_new).keys())),  # persistent
                        choice(list(new_dels.keys())),  # new
                    ]
                    accounts_to_send_from = [self.get_account_with_d_id(d_id) for d_id in d_ids]
                    t_d_ids, request_data_list = zip(*[self.create_next_txn(
                        accounts_to_send_from[j]['account'],
                        accounts_to_send_from[j]['public'],
                        accounts_to_send_from[j]['private'],
                        g_account,
                        d_id,
                        1
                    ) for j, d_id in enumerate(d_ids)])
                    assert set(d_ids) == set(t_d_ids), '{} != {} !!!'.format(d_ids, t_d_ids)  # sanity check, to be removed

                    for j, d_id in enumerate(d_ids):
                        q.put((j, d_id, request_data_list[j]))
                    print(request_data_list)
                    _ = self.process_request_queue(q, d_ids, request_data_list, num_worker_threads)

                    for j, request_data in enumerate(request_data_list):
                        should_accept = event_del_accept[i][j]
                        if should_accept:
                            account_addr = accounts_to_send_from[j]['account']
                            retries, max_retries = 0, 10
                            while True:
                                try:
                                    self.update_account_frontier(account_addr=account_addr)
                                    assert self.account_frontiers[account_addr]['frontier'] == request_data['hash']
                                    break
                                except LogosRPCError as e:
                                    print(e.__dict__)
                                except AssertionError:
                                    pass
                                retries += 1
                                if retries >= max_retries:
                                    print('\nMax retries reached!')
                                    return False
                                sleep(2)

                        # manual inspection debugging, to remove
                        all_lines = self.log_handler.grep_lines(request_data['hash'])
                        pprint_log_lines(all_lines)

                    # Clear event
                    desired_counts.pop(i)
                # keep on waiting

            if not desired_counts:  # All events have taken place
                print('\nCount matched')
                break
            if time() - t0 > timeout:
                print('\nTimed out!')
                return False
            counter = counter % 3 + 1
            sleep(2)

        # Examine transactions and verify that epoch numbers are correct
        return True

        # TODO: test delay scenario & test various invalid epoch number scenarios

    def get_account_with_d_id(self, d_id):
        """
        Get account whose next transaction should be processed by `d_id` as primary
        from already created accounts (local). If none exists, return genesis account

        Args:
            d_id (int): id of delegate whose primary processing capability we want to test

        Returns:
            dict: consisting of keys `account`, `private`, and `public` for matching account
        """
        assert (isinstance(d_id, int) and 0 <= d_id < self.num_delegates)
        try:
            # note that this relies on a correct local frontier record
            account_dict = next(self.accounts[v['i']] for v in self.account_frontiers.values()
                                if designated_delegate(self.accounts[v['i']]['public'], v['frontier']) == d_id)
            return account_dict
        except StopIteration:
            sys.stderr.write('No available account with designated delegate id of {}, returning genesis\n'.format(d_id))
            return {
                'account': g_account,
                'private': g_prv,
                'public': g_pub,
            }
