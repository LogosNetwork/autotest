import os
import paramiko
from queue import Queue, Empty
import random
import re
import requests
import sys
import threading
from time import sleep, time

RPC_PORT = 55000
TXA_JSON_PORT = 56001

g_account = 'lgs_3e3j5tkog48pnny9dmfzj1r16pg8t1e76dz5tmac6iq689wyjfpiij4txtdo'
g_prv = '34F0A37AAD20F4A260F0A5B3CB3D7FB50673212263E58A380BC10474BB039CE4'
g_pub = 'B0311EA55708D6A53C75CDBF88300259C6D018522FE3D4D0A242E431F9E8B6D0'

DUMMY_REP = 'lgs_1111111111111111111111111111111111111111111111111111hifc8npp'

LGS_DEC = 24
MLGS_DEC = 21

MIN_FEE_MLGS = 10
MIN_FEE = str(MIN_FEE_MLGS)+'0'*MLGS_DEC


class LogosRPCError(Exception):

    def __init__(self, uri, message, rpc_error):
        self.uri = uri
        self.message = message
        self.rpc_error = rpc_error

    def __str__(self):
        return 'Received error: {}\nfrom uri {} while calling message\n\t{}'.format(
            self.rpc_error, self.uri, self.message
        )

    __repr__ = __str__


class LogosRpc:
    def __init__(self, ip='', port=RPC_PORT, txa_json_port=TXA_JSON_PORT):
        if ip.find(':') > 0:
            self.ip, self.port = ip.split(':')
        else:
            self.ip = ip
            self.port = port
        # self.txa_json_port = txa_json_port
        self.txa_json_port = RPC_PORT
        self.uri = 'http://{}:{}'.format(self.ip, self.port)
        self.txa_json_uri = 'http://{}:{}'.format(self.ip, self.txa_json_port)

    @staticmethod
    def is_valid_hash(h):
        return isinstance(h, str) and len(h) == 64 and all(isinstance(int(c, 16), int) for c in h)

    # main class function for invoking RPC calls
    def call(self, rpc_action, **kwargs):
        message = {'rpc_action': rpc_action, **kwargs}
        #uri = self.txa_json_uri if action == 'process' else self.uri
        resp = requests.post(self.uri, json=message, headers={'Content-Type': 'application/json'})
        res = resp.json()
        if 'error' in res:
            raise LogosRPCError(self.uri, message, res['error'])
        return res

    def uri(self):
        return self.uri

    def account_info(self, account=g_account):
        return self.call('account_info', account=account)

    def account_history(self, account=g_account, raw=True, count=100, head=''):
        msg = {'account': account, 'raw': 'true' if raw else 'false', 'count': count}
        if head:
            assert self.is_valid_hash(head)
            msg['head'] = head
        return self.call('account_history', **msg)

    def accounts_exist(self, accounts):
        return self.call('accounts_exist', accounts=accounts)

    def key_create(self):
        return self.call('key_create')

    def key_expand(self, key):
        return self.call('key_expand', key=key)

    def block_create(self, txns, previous, type="send", private_key=g_prv, representative=DUMMY_REP, fee_mlgs=MIN_FEE_MLGS):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            representative=representative,
            previous=previous,
            fee=str(fee_mlgs) + '0' * MLGS_DEC,
            transactions=txns,
            work='{0}'.format(random.randint(0, 1000000000)),
        )
    
    def block_create_issuance(self, private_key, symbol, name, total_supply="2100000000000000", type="issuance", fee=MIN_FEE, controllers=[], settings=[], previous="00000000000000000000000000000000", fee_type='flat', fee_rate=0):
        return self.call(
            'block_create',
            type=type,
            total_supply=total_supply,
            symbol=symbol,
            name=name,
            fee_type=fee_type,
            fee_rate=fee_rate,
            issuer_info='',
            private_key=private_key,
            previous=previous,
            fee=str(fee),#+'0'*MLGS_DEC,
            controllers=controllers,
            settings=settings,
            work='{0}'.format(random.randint(0, 1000000000))
        )

    def block_create_distribute(self, previous, private_key, token_id, type="distribute", representative=DUMMY_REP, fee=MIN_FEE, transaction=""):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            transaction=transaction,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )
    
    def block_create_revoke(self, previous, private_key, source, token_id, type="revoke", representative=DUMMY_REP, fee=MIN_FEE, transaction=""):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            source=source,
            transaction=transaction,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )

    def block_create_burn(self, previous, private_key, token_id, amount, type="burn", representative=DUMMY_REP, fee=MIN_FEE):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            amount=amount,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
            )
    
    def block_create_token_send(self, previous, private_key, token_id, type="token_send", representative=DUMMY_REP, fee=MIN_FEE, token_fee='100', transactions=""):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            token_fee=token_fee,
            transactions=transactions,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )

    def block_create_withdraw(self, previous, private_key, token_id, type="distribute", representative=DUMMY_REP, fee=MIN_FEE, transaction=""):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            transaction=transaction,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )

    def block_create_issue_additional(self, previous, private_key, token_id, amount, type="issue_additional", representative=DUMMY_REP, fee=MIN_FEE):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            amount=amount,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )

    def block_create_change_setting(self, previous, private_key, token_id, setting, value, type="change_setting", representative=DUMMY_REP, fee=MIN_FEE):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            setting=setting,
            value=value,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )
    
    def block_create_update_issuer_info(self, previous, private_key, token_id, new_info, type="update_issuer_info", representative=DUMMY_REP, fee=MIN_FEE):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            new_info=new_info,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )

    def block_create_adjust_user_status(self, previous, private_key, token_id, status, account, type="adjust_user_status", fee=MIN_FEE):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            status=status,
            account=account,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )

    def block_create_immute_setting(self, previous, private_key, token_id, setting, type="immute_setting", representative=DUMMY_REP, fee=MIN_FEE):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            setting=setting,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )

    def block_create_adjust_fee(self, previous, private_key, token_id, fee_type, fee_rate, type="adjust_fee", fee=MIN_FEE):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            fee_type=fee_type,
            fee_rate=fee_rate,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )

    def block_create_update_controller(self, previous, private_key, token_id, action, controller, type="update_controller", fee=MIN_FEE):
        return self.call(
            'block_create',
            type=type,
            private_key=private_key,
            previous=previous,
            token_id=token_id,
            action=action,
            controller=controller,
            fee=str(fee),
            work='{0}'.format(random.randint(0, 1000000000))
        )
    
    def process(self, request):
        return self.call('process', request=request)

    def microblock_test(self):
        #self.call('block_create_test')
        return self.call('generate_microblock')

    def epoch_test(self):
        return self.call('generate_epoch')

    def epoch_delegates_current(self):
        return self.call('epoch_delegates', epoch='current')

    def epoch_delegates_next(self):
        return self.call('epoch_delegates', epoch='next')

    def block(self, block_hash):
        assert (self.is_valid_hash(block_hash))
        return self.call('block', hash=block_hash)

    def blocks(self, block_hashes):
        assert (all(self.is_valid_hash(block_hash) for block_hash in block_hashes))
        return self.call('blocks', hashes=block_hashes)

    def blocks_exist(self, block_hashes):
        assert (all(self.is_valid_hash(block_hash) for block_hash in block_hashes))
        return self.call('blocks_exist', hashes=block_hashes)

    def _consensus_blocks(self, type_name, hashes):
        assert type_name in ['request_blocks', 'micro_blocks', 'epochs']
        assert isinstance(hashes, list) and all(self.is_valid_hash(h) for h in hashes)
        return self.call(type_name, hashes=hashes)

    def request_blocks(self, hashes):
        return self._consensus_blocks('request_blocks', hashes)

    def request_blocks_latest(self, delegate_id='0', count='100', head=''):
        call_dict = {'delegate_id': delegate_id, 'count': count}
        if head:
            assert self.is_valid_hash(head)
            call_dict['head'] = head
        return self.call('request_blocks_latest', **call_dict)

    def micro_blocks(self, hashes):
        return self._consensus_blocks('micro_blocks', hashes)

    def micro_blocks_latest(self, count='100', head=''):
        call_dict = {'count': count}
        if head:
            assert self.is_valid_hash(head)
            call_dict['head'] = head
        return self.call('micro_blocks_latest', **call_dict)

    def epochs(self, hashes):
        return self._consensus_blocks('epochs', hashes)

    def epochs_latest(self, count='100', head=''):
        call_dict = {'count': count}
        if head:
            assert self.is_valid_hash(head)
            call_dict['head'] = head
        return self.call('epochs_latest', **call_dict)

    def send_txns(self, dest_addr, source_key=g_prv, source_acct=g_account, count=None, amt_mlgs=None, txns=None,
                  fee_mlgs=MIN_FEE_MLGS):
        info_data = self.account_info(source_acct)
        prev = info_data['frontier']
        blocks_to_process = []
        if txns is not None:
            assert count is None and amt_mlgs is None, 'Cannot supply count and amount while supplying transaction list'
            assert isinstance(txns, list)
        else:
            assert count is not None
            if amt_mlgs is None:
                txns = [str(i + 1) + '0' * MLGS_DEC for i in range(count)]
            else:
                txns = [str(amt_mlgs) + '0' * MLGS_DEC for _ in range(count)]
        for amount in txns:
            create_data = self.block_create(
                txns=[{
                    'amount': amount,
                    'destination': dest_addr
                }],
                previous=prev,
                private_key=source_key,
                fee_mlgs=fee_mlgs
            )
            blocks_to_process.append(create_data)
            prev = create_data['hash']
        process_dataset = [self.process(block_to_process['request']) for block_to_process in blocks_to_process]
        return process_dataset


class RemoteLogsHandler:

    LOG_DIR = '/home/ubuntu/bench/LogosTest/log/'

    def __init__(self, ips, pem_path='{}/.ssh/team-benchmark.pem'.format(os.environ['HOME'])):
        self.ips = ips
        self.num_nodes = len(self.ips)
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.prv_k = paramiko.RSAKey.from_private_key_file(pem_path)

    def get_command_output(self, command, node_id, ssh_client, background=False):
        ssh_client.connect(self.ips[node_id]['PublicIpAddress'], username='ubuntu', pkey=self.prv_k)
        if background:
            transport = ssh_client.get_transport()
            channel = transport.open_session()
            channel.exec_command(command)
            lines = ''
        else:
            ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(command)
            lines = ssh_stdout.read()
            lines = lines.decode("utf-8")
        ssh_client.close()
        return lines.rstrip('\n')

    def execute_parallel_command(self, command, background=False):
        single_command = isinstance(command, str)
        if not single_command:
            assert isinstance(command, list) and \
                   len(command) == self.num_nodes and \
                   all(isinstance(c, str) for c in command)
        all_lines = []
        lines_dict = {}

        def get_command_output_thread(thread_n_id, node_command):
            adhoc_ssh = paramiko.SSHClient()
            adhoc_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            lines_dict[thread_n_id] = self.get_command_output(node_command, thread_n_id, adhoc_ssh, background)

        threads = []
        for i in range(self.num_nodes):
            t = threading.Thread(target=get_command_output_thread, args=(i, command if single_command else command[i]))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        for i in range(self.num_nodes):
            all_lines.append(lines_dict.pop(i))

        return all_lines

    def collect_lines(self, command, node_id=None):
        if node_id is None:
            all_lines = self.execute_parallel_command(command)
        else:
            all_lines = [self.get_command_output(command, node_id, self.ssh)]
        return all_lines

    def grep_lines(self, pattern, node_id=None):
        # can use regex for pattern as well
        command = 'grep -Er "{}" {}*'.format(pattern, RemoteLogsHandler.LOG_DIR)
        return self.collect_lines(command, node_id)

    def grep_count(self, pattern, node_id=None):
        # can use regex for pattern as well
        command = 'grep -Er "{}" {}* | wc -l'.format(pattern, RemoteLogsHandler.LOG_DIR)
        return [int(line.split()[0]) for line in self.collect_lines(command, node_id)]


class LocalLogsHandler:

    LOG_DIR = '../../cloud-benchmark-deployment/deploy/local/DB/'

    def __init__(self, ips):
        self.ips = ips
        self.num_nodes = len(self.ips)

    def get_command_output(self, command, node_id):
        pass

    def collect_lines(self, command, node_id=None):
        pass

    def grep_lines(self, pattern, node_id=None):
        log = max(os.listdir(LocalLogsHandler.LOG_DIR+'Consensus_'+str(node_id)+'/log/'))  
        lines = subprocess.check_output(["grep", "-Er", pattern, LocalLogsHandler.LOG_DIR+'Consensus_'+str(node_id)+'/log/'+log])
        lines_str = lines.decode('utf-8')
        if(lines_str.endswith('\n')):
            return [lines_str[:-1]]
        return [lines.decode('utf-8')]

    def grep_count(self, pattern, node_id=None):
        lines = self.grep_lines(pattern, node_id)[0]
        splitlines = lines.split('\n')
        return len(splitlines)


"""
Various helper functions
"""


def designated_delegate(pub, prev):
    # prev is zero
    indicator = pub if all(c == '0' for c in prev) else prev
    return int(indicator[-2:], 16) % 32


def rerun_needed(method):
    method.rerun_needed = True
    return method


def skip(method):
    method.to_skip = True
    return method


def to_test_name(member_name):
    return member_name.replace('_', ' ').upper()


def pprint_log_lines(all_lines):
    print('\n')
    for i, lines in enumerate(all_lines):
        if not lines:
            continue
        print('NODE {}:'.format(i))
        for line in lines.split('\n'):
            print(line.replace('\\\\', '\\'))


def parse_log_line(line):
    m = re.search(r'\[(.* .*) (.*) (.*)\]: (.*)', line)
    return m.groups()


def batch(iterable, n=1):
    length = len(iterable)
    for idx in range(0, length, n):
        yield iterable[idx:min(idx + n, length)]
