import boto3


def get_remote_cluster_ips(cluster_name='FebruaryTestNet'):
    """
    Creates a dictionary of remote cluster ips
    :param cluster_name: AWS Cloudformation cluster name
    :return: Dictionary of node_id-public_ip key-val pairs
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
    :param node_count: Number of local nodes created
    :return: Dictionary of node_id-public_ip key-val pairs
    """
    return {i: '172.1.1.{}'.format(100 + i) for i in range(node_count)}
