#!/usr/bin/env bash

function usage {
    echo "usage: ./upload_S3.sh [-l /path/to/logos_core] [-a /path/to/agent.py] [-d /path/to/data.ldb] [-c /path/to/bench.json.tmpl] [-r region] [-t custom_tag] [-n]"
    echo "  Uploads one or more of logos binary, agent.py, data.ldb, bench.json.tmpl to S3."
    echo "  Binary will be uploaded to s3://logos-bench/binaries/<iam_username><custom_tag>-<timestamp>/"
    echo "  agent.py will be uploaded to s3://logos-bench/agents/<iam_username><custom_tag>-<timestamp>/"
    echo "  data.ldb will be uploaded to s3://logos-bench/ldbs/<iam_username><custom_tag>-<timestamp>/"
    echo "  bench.json.tmpl will be uploaded to s3://logos-bench/configs/<iam_username><custom_tag>-<timestamp>/"
    echo "  Must upload at least one file."
    echo "  -h  | display help"
    echo "  -l, /path/to/logos_core
      | location of logos_core binary to deploy."
    echo "  -a, /path/to/agent.py
      | location of agent.py to be run on each one of the nodes in a cluster"
    echo "      | if specified, agent.py will be uploaded."
    echo "  -d, /path/to/data.ldb
      | location of data.ldb corresponding to number of nodes to deploy"
    echo "      | if specified, data.ldb will be uploaded."
    echo "  -c, /path/to/bench.json.tmpl
      | location of configuration template"
    echo "      | if specified, bench.json.tmpl will be uploaded."
    echo "  -r, AWS region
      | AWS region for bucket."
    echo "      | defaults to us-east-1"
    echo "  -t, custom_tag
      | custom tag to better identify test version."
    echo "      | defaults to \"\""
    echo "  -n,
      | no-timestamp, indicator that omits time stamp in file suffix."
    echo "      | defaults to false"
    return 0
}

OPTIONS=l:a:d:c:r:t:nh

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
            BINARY_PATH="$2"
            shift 2
            ;;
        -a)
            AGENT_PATH="$2"
            shift 2
            ;;
        -d)
            LDB_PATH="$2"
            shift 2
            ;;
        -c)
            CONF_PATH="$2"
            shift 2
            ;;
        -r)
            REGION="$2"
            shift 2
            ;;
        -t)
            CUSTOM_TAG="$2"
            shift 2
            ;;
        -n)
            NO_TIMESTAMP=true
            shift
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

if [[ -z "$AGENT_PATH" && -z "$LDB_PATH" && -z "$BINARY_PATH" && -z "$CONF_PATH" ]]; then
    echo "Must specify at least one file to upload. "
    invalidOpt=true
fi

if [[ -n "$BINARY_PATH" && ! -f "$BINARY_PATH" ]]; then
    echo "logos_core path is invalid."
    invalidOpt=true
fi

if [[ -n "$AGENT_PATH" && ! -f "$AGENT_PATH" ]]; then
    echo "agent.py path is invalid."
    invalidOpt=true
fi

if [[ -n "$LDB_PATH" && ! -f "$LDB_PATH" ]]; then
    echo "data.ldb path is invalid."
    invalidOpt=true
fi

if [[ -n "$CONF_PATH" && ! -f "$CONF_PATH" ]]; then
    echo "conf.json.tmpl path is invalid."
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

IAM_USER=$(aws iam get-user | python2 -c "import sys, json; print json.load(sys.stdin)['User']['UserName']")
if [[ -n "$NO_TIMESTAMP" ]]; then
    if [[ -n "$CUSTOM_TAG" ]]; then
        FILE_UID="$IAM_USER"-"$CUSTOM_TAG"
    else
        FILE_UID="$IAM_USER"
    fi
    FILE_UID=$(sed 's/_/-/g' <<< ${FILE_UID})
else
    TIMESTAMP=$(date +%s)
    HUMAN_TIME=$(sed 's/ /-/g' <<< $(date -d @${TIMESTAMP}))
    FILE_UID="$IAM_USER""$CUSTOM_TAG"-"$HUMAN_TIME"-"$TIMESTAMP"
    FILE_UID=$(sed 's/_/-/g' <<< ${FILE_UID})
fi


if [[ -n "$BINARY_PATH" ]]; then
    aws s3 cp ${BINARY_PATH} s3://${BUCKET_PREFIX}/binaries/${FILE_UID}/logos_core > /dev/null
    if [[ $? > 0 ]]; then
        echo "Upload to S3 failed, aborting."
        exit 1
    fi
fi

if [[ -n "$AGENT_PATH" ]]; then
    aws s3 cp ${AGENT_PATH} s3://${BUCKET_PREFIX}/agents/${FILE_UID}/agent.py > /dev/null
    if [[ $? > 0 ]]; then
        echo "Upload to S3 failed, aborting."
        exit 1
    fi
fi

if [[ -n "$LDB_PATH" ]]; then
    aws s3 cp ${LDB_PATH} s3://${BUCKET_PREFIX}/ldbs/${FILE_UID}/data.ldb > /dev/null
    if [[ $? > 0 ]]; then
        echo "Upload to S3 failed, aborting."
        exit 1
    fi
fi


if [[ -n "$CONF_PATH" ]]; then
    aws s3 cp ${CONF_PATH} s3://${BUCKET_PREFIX}/configs/${FILE_UID}/bench.json.tmpl > /dev/null
    if [[ $? > 0 ]]; then
        echo "Upload to S3 failed, aborting."
        exit 1
    fi
fi

echo ${FILE_UID}
