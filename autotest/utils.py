import os
import paramiko
import random
import requests

g_account = 'lgs_3e3j5tkog48pnny9dmfzj1r16pg8t1e76dz5tmac6iq689wyjfpiij4txtdo'
g_prv = '34F0A37AAD20F4A260F0A5B3CB3D7FB50673212263E58A380BC10474BB039CE4'
g_pub = 'B0311EA55708D6A53C75CDBF88300259C6D018522FE3D4D0A242E431F9E8B6D0'

DUMMY_REP = 'lgs_1111111111111111111111111111111111111111111111111111hifc8npp'

LGS_DEC = 24
MLGS_DEC = 21

MIN_FEE_MLGS = 10


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
    def __init__(self, ip='', port='55000'):
        if ip.find(':') > 0:
            self.ip, self.port = ip.split(':')
        else:
            self.ip = ip
            self.port = port
        self.uri = 'http://{}:{}'.format(self.ip, self.port)

    @staticmethod
    def is_valid_hash(h):
        return isinstance(h, str) and len(h) == 64 and all(isinstance(int(c, 16), int) for c in h)

    # main class function for invoking RPC calls
    def call(self, action, **kwargs):
        message = {'rpc_action': action, **kwargs}
        resp = requests.post(self.uri, json=message, headers={'Content-Type': 'application/json'})
        res = resp.json()
        if 'error' in res:
            raise LogosRPCError(self.uri, message, res['error'])
        return res

    def uri(self):
        return self.uri

    def account_info(self, account=g_account):
        return self.call('account_info', account=account)
    
    def account_balance(self,account=g_account):
        return self.call('account_balance',account=account)

    def account_history(self, account=g_account, raw=True, count=100, head=''):
        msg = {'account': account, 'raw': 'true' if raw else 'false', 'count': count}
        if head:
            assert self.is_valid_hash(head)
            msg['head'] = head
        return self.call('account_history', **msg)
    
    def candidates(self):
        return self.call('candidates')

    def key_create(self):
        return self.call('key_create')

    def key_expand(self, key):
        return self.call('key_expand', key=key)

    def block_create(self, amount, destination, previous, type="send",key=g_prv, representative=DUMMY_REP, fee_mlgs=MIN_FEE_MLGS, votes=[], transactions=[],bls_key=''):
        return self.call(
            'block_create',
            type=type,
            private_key=key,
            amount=amount,
            transactions=transactions,
            representative=representative,
            previous=previous,
            next=previous,
            votes=votes,
            bls_key=bls_key,
            fee=str(fee_mlgs) + '0' * MLGS_DEC,
            work='{0}'.format(random.randint(0, 1000000000))
        )

    def process(self, request):
        return self.call('process', request=request)

    def microblock_test(self):
        self.call('block_create_test')
        return self.call('generate_microblock')

    def epoch_test(self):
        return self.call('generate_epoch')

    def block(self, block_hash):
        assert (self.is_valid_hash(block_hash))
        return self.call('block', hash=block_hash)

    def blocks(self, block_hashes):
        assert (all(self.is_valid_hash(block_hash) for block_hash in block_hashes))
        return self.call('blocks', hashes=block_hashes)

    def _consensus_blocks(self, type_name, hashes):
        assert type_name in ['batch_blocks', 'micro_blocks', 'epochs']
        assert isinstance(hashes, list) and all(self.is_valid_hash(h) for h in hashes)
        return self.call(type_name, hashes=hashes)

    def batch_blocks(self, hashes):
        return self._consensus_blocks('batch_blocks', hashes)

    def batch_blocks_latest(self, delegate_id='0', count='100', head=''):
        call_dict = {'delegate_id': delegate_id, 'count': count}
        if head:
            assert self.is_valid_hash(head)
            call_dict['head'] = head
        return self.call('batch_blocks_latest', **call_dict)

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
    
    def epoch_latest(self):
        return self.call("epochs_latest",count=1)

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
                amount=amount,
                destination=dest_addr,
                previous=prev,
                key=source_key,
                fee_mlgs=fee_mlgs
            )
            blocks_to_process.append(create_data)
            prev = create_data['hash']
        process_dataset = [self.process(block_to_process['block']) for block_to_process in blocks_to_process]
        return process_dataset

    def get_previous(self,acct):
        info_data = self.account_info(acct)
        return info_data['frontier']


class RemoteLogsHandler:

    LOG_DIR = '/home/ubuntu/bench/LogosTest/log/'

    def __init__(self, ips, pem_path='{}/.ssh/team-benchmark.pem'.format(os.environ['HOME'])):
        self.ips = ips
        self.num_nodes = len(self.ips)
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.prv_k = paramiko.RSAKey.from_private_key_file(pem_path)

    def get_command_output(self, command, node_id):
        self.ssh.connect(self.ips[node_id], username='ubuntu', pkey=self.prv_k)
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(command)
        lines = ssh_stdout.read()
        lines = lines.decode("utf-8")
        self.ssh.close()
        return lines.rstrip('\n')

    def collect_lines(self, command, node_id=None):
        all_lines = []
        if node_id is None:
            for node_id in range(self.num_nodes):
                all_lines.append(self.get_command_output(command, node_id))
        else:
            all_lines.append(self.get_command_output(command, node_id))
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

    def __init__(self, ips):
        self.ips = ips

    def get_command_output(self, command, node_id):
        pass

    def collect_lines(self, command, node_id=None):
        pass

    def grep_lines(self, pattern, node_id=None):
        pass

    def grep_count(self, pattern, node_id=None):
        pass


"""
Various helper functions
"""


def designated_delegate(pub, prev):
    # prev is zero
    indicator = pub if all(map(lambda x: not int(x, 16), prev)) else prev
    return int(indicator[-2:], 16) % 32
