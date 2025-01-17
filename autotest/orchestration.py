import sys
from time import sleep

import boto3
import os
import subprocess

from utils import batch

REGION = 'us-east-1'
BENCH_DIR = '/home/ubuntu/bench'
DATA_PATH = '{}/LogosTest'.format(BENCH_DIR)


def get_remote_cluster_ips(cluster_name='FebruaryTestNet'):
    """
    Creates a dictionary of remote cluster ips

    Args:
        cluster_name (:obj:`str`): AWS Cloudformation cluster name

    Returns:
        dict: Dictionary of node_id: {'PublicIpAddress': public_ip, 'PrivateIpAddress': private_ip} key-val pairs

    """
    client = boto3.client('ec2')
    r_i = client.describe_instances(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    cluster_name,
                ]
            }, {
                'Name': 'instance-state-name',
                'Values': [
                    'running',
                ]
            },
        ],
    )

    ips = {i: v for i, v in enumerate(sorted([
        {k: v for k, v in i.items() if k in ['PrivateIpAddress', 'PublicIpAddress']}
        for rs in r_i['Reservations'] for i in rs['Instances']
    ], key=lambda x: x['PublicIpAddress']))}

    return ips


def get_local_cluster_ips(node_count=32):
    """
    Creates a dictionary of local cluster ips

    Args:
        node_count: (int) Number of local nodes created

    Returns:
        dict: Dictionary of node_id: {'PublicIpAddress': public_ip, 'PrivateIpAddress': private_ip} key-val pairs
    """
    def create_private_public_ip(i):
        fake_addr = '172.1.1.{}'.format(100 + i)
        # Use the same for consistency with remote
        return {'PrivateIpAddress': fake_addr, 'PublicIpAddress': fake_addr}
    ips = {i: create_private_public_ip(i) for i in range(node_count)}
    return ips


def execute_command_on_cluster(cluster_name, commands, client=None, wait=True):
    """
    Runs commands on all instances of a cluster

    Args:
        cluster_name (:obj:`str`): value of `tag:aws:cloudformation:stack-name`
        commands (list(:obj:`str`)): a list of strings, each one a command to execute on the instances
        client: a boto3 ssm client
        wait (bool): whether to wait for command to successfully complete on all nodes

    Returns:
        dict: the response from the send_command function (check the boto3 docs for ssm client.send_command())
    """
    if client is None:
        client = boto3.client('ssm', region_name=REGION)
    command_resp = client.send_command(
        Targets=[
            {
                'Key': 'tag:aws:cloudformation:stack-name',
                'Values': [cluster_name]
            }
        ],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': commands},
        MaxConcurrency='100%',
        OutputS3BucketName='logos-bench-command-log',  # Note: remove if running in other regions than us-east-1!
    )
    command_id = command_resp['Command']['CommandId']
    print('Commands: \n\t{}'.format('\n\t'.join(commands)))
    print('Command id: \n\t{}'.format(command_id))
    if not wait:
        return command_resp
    # poll command execution status
    else:
        # get cluster size first
        cfn_client = boto3.client('cloudformation', region_name=REGION)
        resp = cfn_client.describe_stacks(StackName=cluster_name)
        cluster_size = next(int(p['ParameterValue']) for p in resp['Stacks'][0]['Parameters']
                            if p['ParameterKey'] == 'AsgMaxSize')

        counter = 1
        while True:
            # get status from all instances
            while True:
                resp = client.list_command_invocations(
                    CommandId=command_id,
                )
                status_list = [(i['Status'], i['InstanceId']) for i in resp['CommandInvocations']]
                if status_list:
                    break
                sleep(2)
            # paginate to get remaining list of status, if any
            while 'NextToken' in resp:
                resp = client.list_command_invocations(
                    CommandId=command_id,
                    NextToken=resp['NextToken']
                )
                status_list.extend([(i['Status'], i['InstanceId']) for i in resp['CommandInvocations']])

            # count and report
            err_values = ['Cancelled', 'Failed', 'TimedOut', 'Cancelling']
            n_success = 0
            err = False

            for s in status_list:
                if s[0] == 'Success':
                    n_success += 1
                elif s[0] in err_values:
                    err = True
                    print('Failed to execute command with error status {} on instance {}'.format(*s), file=sys.stderr)

            if err:
                raise RuntimeError('Failed to execute command on remote cluster, original command: \n\t{}'
                                   .format(commands))

            print(' ' * 50, end='\r')
            print('{} out of {} expected Successes{}'.format(n_success, cluster_size, '.' * counter), end='\r')
            counter = counter % 3 + 1
            if n_success == cluster_size:
                print('\nAll succeeded')
                return command_resp

            sleep(2)


def restart_logos(cluster_name, command_line_options='', clear_db=True, client=None):
    """
    Restarts logos_core on remote cluster

    Args:
        cluster_name (:obj:`str`): AWS Cloudformation cluster name
        command_line_options (:obj:`str`): additional command line options for starting logos_core
            (other than --daemon --data_path /home/ubuntu/bench/LogosTest)
        clear_db (bool): whether to wipe database on cluster
        client: a boto3 ssm client

    Returns:
        dict: the response from the send_command function
    """
    files_to_rm = get_files_to_remove(clear_db)
    commands = [
        # 'systemctl stop logos_core',
        'kill -9 $(pgrep logos_core)',
        'rm -f {}'.format(files_to_rm),
        'sleep 20 && ' + gen_start_logos_command(command_line_options)
    ]
    return execute_command_on_cluster(cluster_name, commands, client)


def update_logos(cluster_name, logos_id, command_line_options='', restart=False, clear_db=True, client=None):
    """
    Updates logos_core binary and restarts it on remote cluster

    Args:
        cluster_name (:obj:`str`): AWS Cloudformation cluster name
        logos_id (:obj:`str`): identifier of logos binary on S3 bucket
        command_line_options (:obj:`str`): additional command line options for starting logos_core
            (other than --daemon --data_path /home/ubuntu/bench/LogosTest)
        restart (bool): whether to restart software
        clear_db (bool): whether to wipe database on cluster
        client: a boto3 ssm client

    Returns:
        dict: the response from the send_command function
    """
    files_to_rm = get_files_to_remove(clear_db)
    commands = [
        # 'systemctl stop logos_core',
        'kill -9 $(pgrep logos_core)',
        'aws s3 cp s3://logos-bench-{}/binaries/{}/logos_core {}/logos_core'.format(REGION, logos_id, BENCH_DIR),
        'chmod a+x {}/logos_core'.format(BENCH_DIR),
        'rm -f {}'.format(files_to_rm),
        ('sleep 20 && ' + gen_start_logos_command(command_line_options))if restart else ''
    ]
    return execute_command_on_cluster(cluster_name, commands, client)


def gen_start_logos_command(command_line_options=''):
    """
    Generates bash command for starting logos_core as a systemd service

    Args:
        command_line_options (:obj:`str`): additional command line options for starting logos_core
            (other than --daemon --data_path /home/ubuntu/bench/LogosTest)

    Returns:
        :obj:`str`: bash command string
    """
    # return 'systemctl -f stop logos_core{}'.format(
    #     '_args@\"{}\".service'.format(command_line_options) if command_line_options else '')
    return '/home/ubuntu/bench/logos_core --daemon --data_path /home/ubuntu/bench/LogosTest ' \
           '{} > /dev/null 2>&1 &'.format(command_line_options)


def update_config(cluster_name, config_id='', command_line_options='', restart=False, new_generator=False,
                  clear_db=True, callback=False, callback_args=None, disable_transition=False, client=None):
    """

    Args:
        cluster_name (:obj:`str`): AWS Cloudformation cluster name
        config_id (:obj:`str`): identifier of config template on S3 bucket.
            same config template will be used if this field is not provided
        command_line_options (:obj:`str`): additional command line options for starting logos_core
            (other than --daemon --data_path /home/ubuntu/bench/LogosTest)
        restart (bool): whether to restart software
        new_generator (bool): whether to download latest gen_config.py
        clear_db (bool): whether to wipe database on cluster
        callback (bool): whether to use default callback webhook setup on node 0
        callback_args (dict): dict specifying 'callback_address', 'callback_port', and/or 'callback_target'
        disable_transition (bool): whether to disable epoch transition and only use num_delegate nodes
        client: a boto3 ssm client

    Returns:
        dict: the response from the send_command function
    """
    files_to_rm = get_files_to_remove(clear_db)
    if callback_args is not None:
        assert all(k in ['callback_address', 'callback_port', 'callback_target'] for k in callback_args.keys())
        callback_args_str = ''.join(' --{} {}'.format(k, v) for k, v in callback_args.items())
        callback = True
    else:
        callback_args_str = ''
    if callback:
        callback_str = ' --callback' + callback_args_str
    else:
        callback_str = ''

    commands = [
        'kill -9 $(pgrep logos_core)',
        'aws s3 cp s3://logos-bench-{}/helpers/gen_config.py {}/gen_config.py'.format(REGION, BENCH_DIR)
        if new_generator else '',
        'aws s3 cp s3://logos-bench-{region}/configs/{conf_id}/bench.json.tmpl {bench_dir}/config/bench.json.tmpl'
            .format(
            region=REGION,
            conf_id=config_id,
            bench_dir=BENCH_DIR,
        ) if config_id else '',
        'python {bench_dir}/gen_config.py{callback}{dt} && cp {bench_dir}/config/bench.json {data_path}/config.json'.format(
            bench_dir=BENCH_DIR,
            callback=callback_str,
            dt=' --disable_transition' if disable_transition else '',
            data_path=DATA_PATH
        ),
        'rm -f {}'.format(files_to_rm),
        ('sleep 20 && ' + gen_start_logos_command(command_line_options)) if restart else ''
    ]
    return execute_command_on_cluster(cluster_name, commands, client)


def update_ldb(cluster_name, db_id, command_line_options='', restart=False, client=None):
    """

    Args:
        cluster_name (:obj:`str`): AWS Cloudformation cluster name
        db_id (:obj:`str`): identifier of ldb file on S3 bucket.
        command_line_options (:obj:`str`): additional command line options for starting logos_core
            (other than --daemon --data_path /home/ubuntu/bench/LogosTest)
        restart (bool): whether to restart software
        client: a boto3 ssm client

    Returns:
        dict: the response from the send_command function
    """
    files_to_rm = get_files_to_remove(True)

    commands = [
        'kill -9 $(pgrep logos_core)',
        'rm -f {}'.format(files_to_rm),
        'aws s3 cp s3://logos-bench-{region}/ldbs/{db_id}/data.ldb {data_dir}/ && chmod 644 {data_dir}/data.ldb'.format(
            region=REGION,
            db_id=db_id,
            data_dir=DATA_PATH,
        ),
        ('sleep 20 && ' + gen_start_logos_command(command_line_options)) if restart else ''
    ]
    return execute_command_on_cluster(cluster_name, commands, client)


def get_files_to_remove(clear_db=True):
    """
    Get string of all files to remove before restarting logos_core
    Args:
        clear_db (bool): flag indicating whether to wipe the database

    Returns:
        :obj:`str`: a space separated string of all files to remove
    """
    files_to_rm = '{}/log/*'.format(DATA_PATH)
    if clear_db:
        for db_type in ['data', 'sleeve']:
            files_to_rm += ' {ldb} {ldb}-lock'.format(ldb='{}/{}.ldb'.format(DATA_PATH, db_type))
    return files_to_rm


def run_db_test(cluster_name, client=None):
    commands = [
        'cd {}/../db-tests'.format(BENCH_DIR),
        'python run_test.py {}/LogosTest/data.ldb'.format(BENCH_DIR)
    ]
    return execute_command_on_cluster(cluster_name, commands, client)


def stop_cluster_instances(cluster_name):
    # 1. stop ASG from auto-launching new instances
    asg_name = get_cluster_asg_name(cluster_name)

    asc_client = boto3.client('autoscaling', region_name=REGION)
    _ = asc_client.suspend_processes(
        AutoScalingGroupName=asg_name,
        ScalingProcesses=['Launch'],
    )

    # 2. detach instances from autoscaling group (reduce desired number of instances of asg)
    ec2_client = boto3.client('ec2', region_name=REGION)
    ids_to_stop = get_cluster_instance_ids_by_state(cluster_name, 'running', ec2_client)

    for ids_batch in batch(ids_to_stop, 20):
        _ = asc_client.detach_instances(
            InstanceIds=ids_batch,
            AutoScalingGroupName=asg_name,
            ShouldDecrementDesiredCapacity=True,
        )

    # 3. stop instances
    _ = ec2_client.stop_instances(InstanceIds=ids_to_stop)


def start_cluster_instances(cluster_name):

    # 1. start instances
    ec2_client = boto3.client('ec2', region_name=REGION)

    all_ids = get_cluster_instance_ids_by_state(cluster_name, '', ec2_client)
    counter = 0
    while True:
        ids_to_start = get_cluster_instance_ids_by_state(cluster_name, 'stopped', ec2_client)
        if len(ids_to_start) < len(all_ids):
            print(' ' * 60 + '\r' + 'Waiting for all instances to stop first{}'.format('.' * counter), end='\r')
            counter = counter % 3 + 1
            sleep(5)
        else:
            print('\n')
            break

    _ = ec2_client.start_instances(InstanceIds=ids_to_start)

    # 2. resume ASG auto launch
    asg_name = get_cluster_asg_name(cluster_name)
    asc_client = boto3.client('autoscaling', region_name=REGION)
    _ = asc_client.resume_processes(
        AutoScalingGroupName=asg_name,
        ScalingProcesses=['Launch'],
    )

    # 3. wait till instances are running, attach instances back to autoscaling group
    while True:
        pending_ids = get_cluster_instance_ids_by_state(cluster_name, 'pending', ec2_client)
        if not pending_ids:
            break
        sleep(2)

    for ids_batch in batch(ids_to_start, 20):
        _ = asc_client.attach_instances(
            InstanceIds=ids_batch,
            AutoScalingGroupName=asg_name
        )


def associate_prod_ips(cluster_name):
    ec2 = boto3.client('ec2')
    addrs = ec2.describe_addresses(Filters=[{'Name': 'tag:Name', 'Values': ['TestNet']}])
    addr_allocs = [a['AllocationId'] for a in addrs['Addresses']]
    ec2_ids = get_cluster_instance_ids_by_state(cluster_name)
    for alloc, inst in zip(addr_allocs, ec2_ids):
        ec2.associate_address(AllocationId=alloc, InstanceId=inst)


def get_cluster_instance_ids_by_state(cluster_name, state_name='running', ec2_client=None):
    if ec2_client is None:
        ec2_client = boto3.client('ec2', region_name=REGION)
    filters = [
        {
            'Name': 'tag:aws:cloudformation:stack-name',
            'Values': [cluster_name]
        }
    ]

    if state_name:
        filters.append({
            'Name': 'instance-state-name',
            'Values': [state_name]
        })

    resp = ec2_client.describe_instances(Filters=filters)
    ids = ec2ids_from_resp(resp)
    return ids


def get_cluster_asg_name(cluster_name):
    cfn_client = boto3.client('cloudformation', region_name=REGION)
    asg_name = cfn_client.describe_stack_resource(
        StackName=cluster_name,
        LogicalResourceId='AutoScalingGroup'
    )['StackResourceDetail']['PhysicalResourceId']
    return asg_name


def ec2ids_from_resp(resp):
    return [ins['InstanceId'] for res in resp['Reservations'] for ins in res['Instances']]

def run_db_get(cluster_name, dbname, key, client=None, remote=True):
    if remote:
        commands = [
            'cd {}/../db-tests'.format(BENCH_DIR),
            'python get_from_db.py {}/LogosTest/data.ldb {}/LogosTest/log {} {}'.format(BENCH_DIR, BENCH_DIR, dbname, key)
        ]
        return execute_command_on_cluster(cluster_name, commands, client)
    else:
        print(os.getcwd())
        os.chdir("../../db-tests/")
        print(os.getcwd())
        subprocess.run(["sudo", "python", "get_from_db.py", "../autotest/deploy/local/DB/Consensus_0/data.ldb", "../autotest/deploy/local/DB/Consensus_0/log" , dbname, key])
        os.chdir("../autotest/autotest")
        return
