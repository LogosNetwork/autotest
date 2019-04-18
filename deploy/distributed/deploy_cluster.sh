#!/usr/bin/env bash

function usage {
    echo "usage: ./deploy_bench_cluster_static.sh cluster_name [-l logos_binary_id] [-a agent_id] [-d ldb_id] [-c config_id] [-r region] [-t TTL] [-e ec2_instance_type] [-i IOPS] [-n num_nodes] [--associate] [--public] [-s] [-k key_path]"
    echo "  -h  | display help"
    echo "  cluster_name
      | unique name for cluster to be deployed through Cloudformation"
    echo "  -l, logos_binary_id
      | unique identifier for logos_core binary version"
    echo "      | must exist as a subdirectory inside s3://logos-bench/binaries/, containing the logos_core binary"
    echo "      | if not specified, defaults to last uploaded version."
    echo "  -a, agent_id
      | unique identifier for agent.py version"
    echo "      | must exist as a subdirectory inside s3://logos-bench/agents/, containing the agents.py file"
    echo "      | if not specified, defaults to last uploaded version."
    echo "  -d, ldb_id
      | unique identifier for data.ldb version"
    echo "      | must exist as a subdirectory inside s3://logos-bench/ldbs/, containing the data.ldb file"
    echo "      | if not specified, defaults to last uploaded version."
    echo "  -c, config_id
      | unique identifier for bench.json.tmpl configuration template version"
    echo "      | must exist as a subdirectory inside s3://logos-bench/configs/, containing the bench.json.tmpl file"
    echo "      | if not specified, defaults to last uploaded version."
    echo "  -r, AWS region
      | AWS region to create the stack in"
    echo "      | defaults to us-east-1"
    echo "  -t, TTL
      | time-to-live (in minutes) for the created stack, after which it will auto-delete"
    echo "      | defaults to 120"
    echo "  -e, ec2_instance_type
      | Bench cluster EC2 instance type"
    echo "      | defaults to t2.small"
    echo "  -i, IOPS
      | IOPS for provisioned SSD"
    echo "      | need to be specified if IOPS-provisioned instances are desired"
    echo "  -n, num_nodes
      | number of nodes in auto scaling group"
    echo "      | defaults to 4"
    echo "  --associate
      | indicator of whether to associate elastic IP address to each node in cluster"
    echo "      | defaults to false"
    echo "  --public
      | indicator of whether to launch public testnet"
    echo "      | defaults to false"
    echo "  -s
      | flag for indicating whether to ssh into the nodes once launched"
    echo "      | if unspecified, defaults to no."
    echo "  -k, /path/to/pem_file
      | path to team-benchmark EC2 key pair .pem file."
    echo "      | required if -s is set"
    return 0
}

OPTIONS=l:a:d:c:r:k:t:e:i:n:sh
LONG_OPTS=associate,public

! PARSED=$(getopt --options=${OPTIONS} --longoptions=${LONG_OPTS} --name "$0" -- "$@")
if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    # getopt has complained about wrong arguments to stdout
    usage
    exit 2
fi

eval set -- "${PARSED}"
TTL="120"
production=false

while true; do
    case "$1" in
        -l)
            LOGOS_ID="$2"
            shift 2
            ;;
        -a)
            AGENT_ID="$2"
            shift 2
            ;;
        -d)
            LDB_ID="$2"
            shift 2
            ;;
        -c)
            CONF_ID="$2"
            shift 2
            ;;
        -r)
            REGION="$2"
            shift 2
            ;;
        -t)
            TTL="$2"
            shift 2
            ;;
        -e)
            INSTANCE_TYPE="$2"
            shift 2
            ;;
        -i)
            IOPS="$2"
            VolSize=$(($(($IOPS-1))/50+1))
            VOLUME_TYPE="io1"
            shift 2
            ;;
        -n)
            NUMBER_OF_NODES="$2"
            shift 2
            ;;
        --associate)
            associate=1
            shift
            ;;
        --public)
            public=1
            associate=1
            production=true
            shift
            ;;
        -s)
            SSH=true
            shift
            ;;
        -k)
            KEY_PATH="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Programming error"
            usage
            exit 3
            ;;
    esac
done

invalidOpt=false

if [[ ! "$TTL" =~ ^[1-9][0-9]*$ ]]; then
    echo "Invalid input value for TTL, must be a valid integer"
    invalidOpt=true
fi

if [[ $# -ne 1 ]]; then
    echo "Must specify valid cluster name."
    invalidOpt=true
else
    CLUSTER_NAME=$1
    aws cloudformation describe-stacks --stack-name ${CLUSTER_NAME} --query "Stacks[].StackName" --output text &> /dev/null
    [[ $? -eq 0 ]] && echo "Cluster already exists. Please use a different name." && invalidOpt=true
fi

if [[ -n "$SSH" ]]; then
    if [[  ! -f "$KEY_PATH"  ]]; then
        echo "Must specify valid file path to team benchmarking EC2 key pair in order to connect to nodes."
        invalidOpt=true
    fi
fi


if [[ ${invalidOpt} = true ]]; then
    usage
    exit 3
fi

if [[ -z "$REGION" ]]; then
    REGION="us-east-1"
fi

BUCKET_SUFFIX="-$REGION"


function get_id () {
    aws s3api list-objects --bucket "logos-bench$BUCKET_SUFFIX" --prefix "$1" --query 'Contents[][].{Key: Key, LastModified: LastModified}' --output json \
        | python2.7 -c "import json, sys; from datetime import datetime; data=json.load(sys.stdin);\
        val=sorted(data, key=lambda x: datetime.strptime(x['LastModified'], '%Y-%m-%dT%H:%M:%S.%fZ'), reverse=True)[0]\
        ['Key'].split('/')[1] if data else 'false';\
        print val"
}

if [[ -z "$INSTANCE_TYPE" ]]; then
    echo "Instance type not specified, defaulting to t2.small."
    INSTANCE_TYPE="t2.small"
fi
INSTANCE_CLASS=$(echo "$INSTANCE_TYPE" | cut -d'.' -f 1)
NVMe=false
[[ "$INSTANCE_CLASS" == "i3" ]] && NVMe=true


if [[ -z "$VOLUME_TYPE" ]]; then
    echo "IOPS not specified, defaulting to use General Purpose (gp2) SSD for EBS volume type."
    VOLUME_TYPE="gp2"
    IOPS="120"
    VolSize="40"
fi

if [[ -z "$LOGOS_ID" ]]; then
    echo "logos binary id not specified, defaulting to last modified one."
    LOGOS_ID=$(get_id binaries)
    echo "    ${LOGOS_ID}"
fi
# check if bucket subdirectory actually exists
if [[ ! $(aws s3 ls s3://logos-bench"$BUCKET_SUFFIX"/binaries/ | grep "PRE $LOGOS_ID/") ]]; then
    echo "logos version id does not exist. Subdirectory must be under s3://logos-bench/binaries/"
    exit 1
fi

if [[ -z "$AGENT_ID" ]]; then
    echo "agent.py id not specified, defaulting to last modified one."
    AGENT_ID=$(get_id agents)
    echo "    ${AGENT_ID}"
fi
# check if bucket subdirectory actually exists
if [[ ! $(aws s3 ls s3://logos-bench"$BUCKET_SUFFIX"/agents/ | grep "PRE $AGENT_ID/") ]]; then
    echo "agent.py version id does not exist. Subdirectory must be under s3://logos-bench/agents/"
    exit 1
fi

if [[ -z "$LDB_ID" ]]; then
    echo "data.ldb id not specified, defaulting to last modified one."
    LDB_ID=$(get_id ldbs)
    echo "    ${LDB_ID}"
fi
# check if bucket subdirectory actually exists
if [[ ! $(aws s3 ls s3://logos-bench"$BUCKET_SUFFIX"/ldbs/ | grep "PRE $LDB_ID/") ]]; then
    echo "data.ldb version id does not exist. Subdirectory must be under s3://logos-bench/ldbs/"
    exit 1
fi

if [[ -z "$CONF_ID" ]]; then
    echo "bench.json.tmpl id not specified, defaulting to last modified one."
    CONF_ID=$(get_id configs)
    echo "    ${CONF_ID}"
fi
# check if bucket subdirectory actually exists
if [[ ! $(aws s3 ls s3://logos-bench"$BUCKET_SUFFIX"/configs/ | grep "PRE $CONF_ID/") ]]; then
    echo "bench.json.tmpl id does not exist. Subdirectory must be under s3://logos-bench/configs/"
    exit 1
fi

if [[ -z "$NUMBER_OF_NODES" ]]; then
    echo "Number of nodes was not specified, defaulting to 4."
    NUMBER_OF_NODES=4
fi

# ========================================================================================
# Done with argparse, begin bash script execution
# ========================================================================================
# Get directory of the build.sh script
OLD_PWD=${PWD}
BUILD_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

JSON_FILE_NAME="stack"

aws --region "${REGION}" cloudformation create-stack --stack-name "${CLUSTER_NAME}" \
    --capabilities CAPABILITY_IAM \
    --template-body file://${BUILD_DIR}/"${JSON_FILE_NAME}".json \
    --parameters \
        ParameterKey=LogosVersion,ParameterValue=${LOGOS_ID} \
        ParameterKey=AgentVersion,ParameterValue=${AGENT_ID} \
        ParameterKey=StackTTL,ParameterValue=${TTL} \
        ParameterKey=LDBVersion,ParameterValue=${LDB_ID} \
        ParameterKey=ConfVersion,ParameterValue=${CONF_ID} \
        ParameterKey=ProductionFlag,ParameterValue=${production} \
        ParameterKey=AsgMaxSize,ParameterValue=${NUMBER_OF_NODES} \
        ParameterKey=InstanceType,ParameterValue=${INSTANCE_TYPE} \
        ParameterKey=VolumeType,ParameterValue=${VOLUME_TYPE} \
        ParameterKey=VolSize,ParameterValue=${VolSize} \
        ParameterKey=IOPS,ParameterValue=${IOPS} \
        ParameterKey=NVMe,ParameterValue=${NVMe}
[[ $? > 0 ]] && echo "Stack creation failed." && exit 1
sleep 2

statusList="CREATE_COMPLETE CREATE_IN_PROGRESS"
while true; do
    status=$(aws --region ${REGION} cloudformation describe-stacks --stack-name ${CLUSTER_NAME} --query Stacks[0].StackStatus)
    status=$(sed 's/\"//g' <<< ${status})
    if echo ${status} | grep "CREATE_COMPLETE" > /dev/null; then
        echo "Creation complete."
        peer_instances=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=$CLUSTER_NAME" "Name=instance-state-name,Values=running" --query Reservations[].Instances[].InstanceId --output text)
        if [[ -n "${associate}" ]]; then
            echo "Associate Elastic IP addresses to nodes in cluster."
            eipallocs=$(aws ec2 describe-addresses --filters Name=tag:Name,Values=TestNet --query Addresses[].AllocationId --output text)
            eipallocs_arr=(${eipallocs})
            instance_id_arr=(${peer_instances})
            for i in `seq 1 ${NUMBER_OF_NODES}`; do
                aws ec2 associate-address --allocation-id ${eipallocs_arr[$((${i}-1))]} --instance-id ${instance_id_arr[$((${i}-1))]} --allow-reassociation --query AssociationId --output text
            done
            # need to regenerate config files on each node and restart software
            aws ssm send-command --document-name "AWS-RunShellScript" --targets '{"Key":"tag:aws:cloudformation:stack-name","Values":["'"$CLUSTER_NAME"'"]}' --max-concurrency "100%" --parameters '{"commands":["atrm 1", "systemctl stop logos_core", "'"aws s3 cp s3://logos-bench-$REGION/binaries/$LOGOS_ID/logos_core /home/ubuntu/bench/logos_core && chmod 700 /home/ubuntu/bench/logos_core && rm -f /home/ubuntu/bench/LogosTest/log/* /home/ubuntu/bench/LogosTest/data.ldb /home/ubuntu/bench/LogosTest/data.ldb-lock"'", "'"aws s3 cp s3://logos-bench-$REGION/helpers/gen_config.py /home/ubuntu/bench/gen_config.py && python /home/ubuntu/bench/gen_config.py --callback && cp /home/ubuntu/bench/config/bench.json /home/ubuntu/bench/LogosTest/config.json"'", "sleep 5 && systemctl start logos_core"],"executionTimeout":["3600"],"workingDirectory":["/home/ubuntu/"]}' --timeout-seconds 600 --region us-east-1 --query Command.CommandId --output text
        fi
        peer_ips=$(aws ec2 describe-instances --instance-ids ${peer_instances} --query 'Reservations[].Instances[].NetworkInterfaces[].Association.PublicIp' --output text)
        peer_ips=$(sed 's/ /,/g' <<< ${peer_ips})
        echo ${peer_ips}
        # start node software
#        ${BUILD_DIR}/start_logos_core.sh ${CLUSTER_NAME}
        # If in VNC viewer mode, launch new windows and ssh in
        if [[  -n "${DISPLAY}" && -n "${SSH}" ]]; then
            if ! [[ -x "$(command -v wmctrl)" ]]; then
                echo "wmctrl not found. Installing..."
                sudo apt-get install -y wmctrl
            fi
            counter=0
            # get screen dimension
            dim=$(xdpyinfo | grep dimensions | sed -r 's/^[^0-9]*([0-9]+x[0-9]+).*$/\1/')
            width=$(echo $dim | cut -d'x' -f1)
            height=$(echo $dim | cut -d'x' -f2)
            window_width=$(($width/4))
            window_height=$(($height*15/32))
            n_col=$(($window_width/9-10))
            n_row=$(($window_height/18-10))
            for ip in $(echo ${peer_ips} | sed "s/,/ /g"); do
                # set workspace, xpos, ypos for each window
                workspace=$(($counter/8))
                xpos=$(($counter%4*$window_width))
                ypos=$(($counter/4%2*$height/2))
                xfce4-terminal -H -e "ssh -o 'StrictHostKeyChecking no' -i ${KEY_PATH} ubuntu@${ip}" --title=dt${counter}&
                sleep 0.5
                wmctrl -r dt${counter} -e 0,${xpos},${ypos},${window_width},${window_height}
                wmctrl -r dt${counter} -t ${workspace}
                let counter+=1
            done
        fi
        exit 0
    fi
    if ! echo "$statusList" | grep -w "$status" > /dev/null; then
        echo "Unexpected status: $status."
        exit 1
    fi
    sleep 10
done