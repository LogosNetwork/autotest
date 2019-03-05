import clilib as rpc
import sys

nodes = ['172.1.1.100']
secondary = False
primary = False

msg = {'rpc_action':'generate_microblock'}
i = 1
while i < len(sys.argv):
  if sys.argv[i] == '--epoch':
    msg['last'] = 'true';
  elif sys.argv[i] == '--secondary':
    secondary = True
  elif sys.argv[i] == '--primary':
    primary = True
  elif sys.argv[i] == '--nodes':
    nodes = []
    with open(sys.argv[i+1]) as f:
      for l in f:
        nodes.append(l.rstrip('\n'))
    i += 1
  elif sys.argv[i] == '--node-id':
      nodes = []
      i += 1
      nodes.append('172.1.1.1'+sys.argv[i])
  else:
    raise "invalid argument"
  i += 1

if secondary:
  nodes = nodes[1:]
if primary:
  nodes = nodes[0:1]

if len(nodes) == 0:
  raise Exception("no nodes")

for ip in nodes:
  print(ip)
  node = rpc.LogosRpc(ip)
  res = node.call(msg);
  print(res)
