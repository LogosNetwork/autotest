#!/usr/bin/env bash

function usage {
    echo "usage: ./update_remote_file.sh cluster_name [-l logos_binary_id] [-a agent_id] [-d ldb_id] [-c config_id] [-r region]"
    echo "  Update one or more of logos binary, agent.py, data.ldb, and bench.json.tmpl"
    echo "  -h  | display help"
    echo "  cluster_name
      | unique name for cluster to be updated (must be already deployed through Cloudformation)"
    echo "  -l, logos_binary_id
      | unique identifier for logos_core binary version"
    echo "      | must exist as a subdirectory inside s3://logos-bench-<aws-region>/binaries/, containing the logos_core binary"
    echo "  -a, agent_id
      | unique identifier for agent.py version"
    echo "      | must exist as a subdirectory inside s3://logos-bench-<aws-region>/agents/, containing the agent.py file"
    echo "  -d, ldb_id
      | unique identifier for data.ldb version"
    echo "      | must exist as a subdirectory inside s3://logos-bench-<aws-region>/ldbs/, containing the data.ldb file"
    echo "  -c, config_id
      | unique identifier for bench.json.tmpl configuration template version"
    echo "      | must exist as a subdirectory inside s3://logos-bench-<aws-region>/configs/, containing the bench.json.tmpl file"
    echo "  -r, AWS region
      | AWS region for stack and its corresponding bucket"
    echo "      | defaults to us-east-1"
    return 0
}

OPTIONS=l:a:d:c:r:h

! PARSED=$(getopt --options=${OPTIONS} --name "$0" -- "$@")
if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    # getopt has complained about wrong arguments to stdout
    usage
    exit 2
fi

eval set -- "${PARSED}"

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

if [[ $# -ne 1 ]]; then
    echo "Must specify cluster name."
    invalidOpt=true
else
    CLUSTER_NAME=$1
    if [[ ! $(aws ec2 describe-instances --query 'Reservations[].Instances[].Tags[?Key==`Name`].Value' --output text | grep ${CLUSTER_NAME}) ]]; then
        echo "Cluster doesn't exist. Please provide a valid identifier."
        invalidOpt=true
    fi
fi

if [[ -z "$LOGOS_ID" && -z "$LDB_ID" && -z "$CONF_ID" && -z "$AGENT_ID" ]]; then
    echo "Must specify at least one file to update. "
    invalidOpt=true
fi

if [[ ${invalidOpt} = true ]]; then
    usage
    exit 3
fi

if [[ -z "$REGION" ]]; then
    echo "defaulting region to us-east-1"
    REGION="us-east-1"
fi
BUCKET_PREFIX="logos-bench-$REGION"

# ========================================================================================
# Done with argparse, begin bash script execution
# ========================================================================================

function poll_command_status () {
    commandId=$1
    echo ${commandId}
    n=$2
    while true; do
        statusDetails=$(aws ssm list-command-invocations --command-id ${commandId} --query "CommandInvocations[].StatusDetails" --output text)
        echo "Command status: ${statusDetails}"
        n_commands=$(echo ${statusDetails} | wc -w)
        [[ "$n_commands" -eq "$n" ]] || waiting=true
        for i in ${statusDetails}; do
            waiting=false
            if [[ "Success" != "$i" ]]; then
                waiting=true
                break
            fi
        done
        [[ ${waiting} = true ]] || break
        sleep 5
    done
}

n_nodes=$(aws cloudformation describe-stacks --stack-name ${CLUSTER_NAME} --query "Stacks[0].Parameters[? ParameterKey=='AsgMaxSize'].ParameterValue" --output text)

if [[ -n "$LOGOS_ID" ]]; then
    if [[ ! $(aws s3 ls s3://${BUCKET_PREFIX}/binaries/ | grep "PRE $LOGOS_ID/") ]]; then
        echo "logos version id does not exist. Subdirectory must be under s3://${BUCKET_PREFIX}/binaries/"
        exit 1
    fi
    echo "Updating Logos binary..."
    commandId=$(aws ssm send-command --document-name "AWS-RunShellScript" --targets '{"Key":"tag:aws:cloudformation:stack-name","'"Values"'":["'"$CLUSTER_NAME"'"]}' --max-concurrency "100%" --parameters '{"commands":["systemctl stop logos_core", "'"aws s3 cp s3://${BUCKET_PREFIX}/binaries/$LOGOS_ID/logos_core /home/ubuntu/bench/logos_core"'","chmod a+x /home/ubuntu/bench/logos_core", "sleep 20 && systemctl start logos_core"],"executionTimeout":["3600"],"workingDirectory":["/home/ubuntu/"]}' --timeout-seconds 600 --output-s3-bucket-name "logos-bench-command-log" --region ${REGION} --query "Command.CommandId" --output text)
    poll_command_status ${commandId} ${n_nodes}
fi

if [[ -n "$LDB_ID" ]]; then
    if [[ ! $(aws s3 ls s3://${BUCKET_PREFIX}/ldbs/ | grep "PRE $LDB_ID/") ]]; then
        echo "data.ldb version id does not exist. Subdirectory must be under s3://${BUCKET_PREFIX}/ldbs/"
        exit 1
    fi
    echo "Updating data.ldb..."
    commandId=$(aws ssm send-command --document-name "AWS-RunShellScript" --targets '{"Key":"tag:aws:cloudformation:stack-name","'"Values"'":["'"$CLUSTER_NAME"'"]}' --max-concurrency "100%" --parameters '{"commands":["'"aws s3 cp s3://${BUCKET_PREFIX}/ldbs/$LDB_ID/data.ldb /home/ubuntu/bench/config/data.ldb"'","chmod 644 /home/ubuntu/bench/config/data.ldb && rm -f /home/ubuntu/bench/LogosTest/data.ldb /home/ubuntu/bench/LogosTest/data.ldb-lock && cp /home/ubuntu/bench/config/data.ldb /home/ubuntu/bench/LogosTest/ && systemctl restart logos_core"],"executionTimeout":["3600"],"workingDirectory":["/home/ubuntu/"]}' --timeout-seconds 600 --output-s3-bucket-name "logos-bench-command-log" --region ${REGION} --query "Command.CommandId" --output text)
    poll_command_status ${commandId} ${n_nodes}
fi

if [[ -n "$CONF_ID" ]]; then
    if [[ ! $(aws s3 ls s3://${BUCKET_PREFIX}/configs/ | grep "PRE $CONF_ID/") ]]; then
        echo "bench.json.tmpl version id does not exist. Subdirectory must be under s3://${BUCKET_PREFIX}/configs/"
        exit 1
    fi
    echo "Updating bench.json.tmpl and regenerating config.json"
    commandId=$(aws ssm send-command --document-name "AWS-RunShellScript" --targets '{"Key":"tag:aws:cloudformation:stack-name","'"Values"'":["'"$CLUSTER_NAME"'"]}' --max-concurrency "100%" --parameters '{"commands":["'"aws s3 cp s3://${BUCKET_PREFIX}/configs/$CONF_ID/bench.json.tmpl /home/ubuntu/bench/config/bench.json.tmpl"'","systemctl stop logos_core","chmod 666 /home/ubuntu/bench/config/bench.json.tmpl","python /home/ubuntu/bench/gen_config.py && cp /home/ubuntu/bench/config/bench.json /home/ubuntu/bench/LogosTest/config.json && chmod 666 /home/ubuntu/bench/LogosTest/config.json && sleep 10 && systemctl restart logos_core"],"executionTimeout":["3600"],"workingDirectory":["/home/ubuntu/"]}' --timeout-seconds 600 --output-s3-bucket-name "logos-bench-command-log" --region ${REGION} --query "Command.CommandId" --output text)
    poll_command_status ${commandId} ${n_nodes}
fi

if [[ -n "$AGENT_ID" ]]; then
    if [[ ! $(aws s3 ls s3://${BUCKET_PREFIX}/agents/ | grep "PRE $AGENT_ID/") ]]; then
        echo "agent.py id does not exist. Subdirectory must be under s3://${BUCKET_PREFIX}/agents/"
        exit 1
    fi
    echo "Updating agent.py..."
    commandId=$(aws ssm send-command --document-name "AWS-RunShellScript" --targets '{"Key":"tag:aws:cloudformation:stack-name","'"Values"'":["'"$CLUSTER_NAME"'"]}' --max-concurrency "100%" --parameters '{"commands":["pkill -9 -f agent.py","systemctl stop logos_core","'"aws s3 cp s3://${BUCKET_PREFIX}/agents/$AGENT_ID/agent.py /home/ubuntu/bench/agent.py"'","chmod a+x /home/ubuntu/bench/agent.py","python /home/ubuntu/bench/agent.py &","sleep 5","ls","echo done"],"executionTimeout":["3600"],"workingDirectory":["/home/ubuntu/"]}' --timeout-seconds 600 --output-s3-bucket-name "logos-bench-command-log" --region ${REGION} --query "Command.CommandId" --output text)
    echo ${commandId}
fi

exit 0
