import sys
from time import sleep

import boto3

REGION = 'us-east-1'
BENCH_DIR = '/home/ubuntu/bench'
DATA_PATH = '{}/LogosTest'.format(BENCH_DIR)


def get_remote_cluster_ips(cluster_name='FebruaryTestNet'):
    """
    Creates a dictionary of remote cluster ips

    Args:
        cluster_name (:obj:`str`): AWS Cloudformation cluster name

    Returns:
        dict: Dictionary of node_id-public_ip key-val pairs

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

    ips = sorted([i['PublicIpAddress'] for rs in r_i['Reservations'] for i in rs['Instances']])

    return {i: v for i, v in enumerate(ips)}


def get_local_cluster_ips(node_count=32):
    """
    Creates a dictionary of local cluster ips

    Args:
        node_count: (int) Number of local nodes created

    Returns:
        dict: Dictionary of {`node_id`: `public_ip`} key-val pairs
    """
    return {i: '172.1.1.{}'.format(100 + i) for i in range(node_count)}


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


def restart_logos(cluster_name, clear_db=True, client=None):
    """
    Restarts logos_core on remote cluster

    Args:
        cluster_name (:obj:`str`): AWS Cloudformation cluster name
        clear_db (bool): whether to wipe database on cluster
        client: a boto3 ssm client

    Returns:
        dict: the response from the send_command function
    """
    files_to_rm = get_files_to_remove(clear_db)
    commands = [
        'systemctl stop logos_core',
        'rm -f {}'.format(files_to_rm),
        'sleep 20 && systemctl start logos_core'
    ]
    return execute_command_on_cluster(cluster_name, commands, client)


def update_logos(cluster_name, logos_id, clear_db=True, client=None):
    """

    Args:
        cluster_name (:obj:`str`): AWS Cloudformation cluster name
        logos_id (:obj:`str`): identifier of logos binary on S3 bucket
        clear_db (bool): whether to wipe database on cluster
        client: a boto3 ssm client

    Returns:

    """
    files_to_rm = get_files_to_remove(clear_db)
    commands = [
        'systemctl stop logos_core',
        'aws s3 cp s3://logos-bench-{}/binaries/{}/logos_core {}/logos_core'.format(REGION, logos_id, BENCH_DIR),
        'chmod a+x {}/logos_core'.format(BENCH_DIR),
        'rm -f {}'.format(files_to_rm),
        'sleep 20 && systemctl start logos_core'
    ]
    return execute_command_on_cluster(cluster_name, commands, client)


def update_config(cluster_name, config_id, new_generator=False, clear_db=True, callback=False,
                  callback_args=None, client=None):
    """

    Args:
        cluster_name (:obj:`str`): AWS Cloudformation cluster name
        config_id (:obj:`str`): identifier of config template on S3 bucket
        new_generator (bool): whether to download latest gen_config.py
        clear_db (bool): whether to wipe database on cluster
        callback (bool): whether to use default callback webhook setup on node 0
        callback_args (dict): dict specifying 'callback_address', 'callback_port', and/or 'callback_target'
        client: a boto3 ssm client

    Returns:

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
        'systemctl stop logos_core',
        'aws s3 cp s3://logos-bench-{}/helpers/gen_config.py {}/gen_config.py'.format(REGION, BENCH_DIR)
        if new_generator else '',
        'aws s3 cp s3://logos-bench-{region}/configs/{conf_id}/bench.json.tmpl {bench_dir}/config/bench.json.tmpl && '
        'python {bench_dir}/gen_config.py{callback} && cp {bench_dir}/config/bench.json {data_path}/config.json'.format(
            region=REGION,
            conf_id=config_id,
            bench_dir=BENCH_DIR,
            callback=callback_str,
            data_path=DATA_PATH
        ),
        'rm -f {}'.format(files_to_rm),
        'sleep 20 && systemctl start logos_core'
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
        files_to_rm += ' {ldb} {ldb}-lock'.format(ldb='{}/data.ldb'.format(DATA_PATH))
    return files_to_rm
