import argparse
import json
import os
import re
from time import sleep

import boto3
import requests

parser = argparse.ArgumentParser()
parser.add_argument('--callback', action='store_true')
parser.add_argument('--callback_address', default='pla.bs')
parser.add_argument('--callback_port', default='80')
parser.add_argument('--callback_target', default='/callback')

args = parser.parse_args()

sleep(3)

config_dir = '/home/ubuntu/bench/config/'
# config_dir = '/Users/shangyan/Desktop/Logos/codebase/cloud-benchmark-deployment/bench_files/'
config_tmpl_path = os.path.join(config_dir, 'bench.json.tmpl')
with open(config_tmpl_path) as f:
    config_template = f.read()

while True:
    try:
        resp = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
        info = json.loads(resp.text)
        private_ip = info['privateIp']
        region = info['region']
        instance_id = info["instanceId"]
        print("instance id: {}".format(instance_id))
        break
    except Exception as e:
        print(e)
        sleep(3)

while True:
    ec2_rsrc = boto3.resource('ec2', region_name=region)
    try:
        instance = ec2_rsrc.Instance(instance_id)
        stack_name = list(filter(lambda d: d['Key'] == 'aws:cloudformation:stack-name', instance.tags))[0]['Value']
        print("stack name: {}".format(stack_name))
        break
    except Exception as e:
        print(e)
        sleep(3)

while True:
    try:
        cloudformation = boto3.resource('cloudformation', region_name=region)
        stack = cloudformation.Stack(stack_name)
        n_nodes = int(list(filter(lambda d: d['ParameterKey'] == 'AsgMaxSize', stack.parameters))[0]['ParameterValue'])
        print("number of nodes in stack: {}".format(n_nodes))
        break
    except Exception as e:
        print(e)
        sleep(3)

while True:
    try:
        ec2_client = boto3.client('ec2', region_name=region)
        peers = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:aws:cloudformation:stack-name',
                    'Values': [stack_name]
                }, {
                    'Name': 'instance-state-name',
                    'Values': ['running']
                }
            ]
        )
        peer_ip_dicts = sorted([
            {k: v for k, v in i.items() if k in ['PrivateIpAddress', 'PublicIpAddress']}
            for rs in peers['Reservations'] for i in rs['Instances']
        ], key=lambda x: x['PublicIpAddress'])
        n_awake = len(peer_ip_dicts)
        if n_awake < n_nodes:
            print("{} / {} awake".format(n_awake, n_nodes))
            sleep(3)
        else:
            print("All awake. \t", peer_ip_dicts)
            break
    except Exception as e:
        print(e)
        sleep(3)

delegate_id = str(next((i for i, v in enumerate(peer_ip_dicts) if v['PublicIpAddress'] == instance.public_ip_address)))
delegate_peers = [{"ip_address": v['PrivateIpAddress'], "delegate_id": str(i)} for i, v in enumerate(peer_ip_dicts)]

# delegate_peers = list(filter(lambda d: d['delegate_id'] != delegate_id, delegate_peers))
peering_port = '7075'

config_path = os.path.join(config_dir, 'bench.json')
with open(config_path, 'w') as f:
    new_config = re.sub('{{LOCAL_IP}}', "0.0.0.0", config_template)
    new_config = re.sub('{{LOGOS_LOCAL_IP}}', private_ip, new_config)
    new_config = re.sub('{{PEERING_PORT}}', peering_port, new_config)
    new_config = re.sub('{{DELEGATE_ID}}', delegate_id, new_config)
    new_config = re.sub('{{TXA_DEL_IP}}', private_ip, new_config)
    new_config = re.sub('{{TXA_IP}}', private_ip, new_config)
    new_config = re.sub('{{PEERS}}', json.dumps(delegate_peers, indent=4), new_config)
    new_config = json.loads(new_config)
    if args.callback and delegate_id == '0':
        new_config['node']['callback_address'] = args.callback_address
        new_config['node']['callback_port'] = args.callback_port
        new_config['node']['callback_target'] = args.callback_target
    json.dump(new_config, f, indent=4)
print(new_config)
