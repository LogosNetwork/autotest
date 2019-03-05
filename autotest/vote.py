from test_election import *
from run_test import *
ip = "172.1.1.1"+sys.argv[1]
start = int(sys.argv[2])

node = LogosRpc(ip)


for x in range(start,start+8):
    prev = node.get_previous(accounts[x])
    b = node.block_create(0,0,prev,type='election_vote',key=prv_keys[x],votes={accounts[x]:8})
    res = node.process(b['request'])
    if 'error' in res:
        print(res['error'])
    else:
        print(res)
