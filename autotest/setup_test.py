import boto3


def get_remote_cluster_ips(cluster_name='FebruaryTestNet'):
    client = boto3.client('ec2')
    r_i = client.describe_instances(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [
                    cluster_name,
                ]
            },{
                'Name': 'instance-state-name',
                'Values': [
                    'running',
                ]
            },
        ],
    )

    ips = sorted([i['PublicIpAddress'] for rs in r_i['Reservations'] for i in rs['Instances']])

    return {i: v for i, v in enumerate(ips)}
