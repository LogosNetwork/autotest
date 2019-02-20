#!/bin/bash

inst=32
tag_name=TestNet
alloc_list=()

for i in `seq 1 ${inst}`; do
    echo "Allocating and tagging Elastic IP at index ${i}."
    alloc_id=$(aws ec2 allocate-address --query AllocationId --output text)
    aws ec2 create-tags --resources ${alloc_id} --tags Key=Name,Value=${tag_name}
    if [[ $? > 0 ]]; then
        echo "Allocation stopped at index ${i}."
    fi
    alloc_list=("${alloc_list[@]}" ${alloc_id})
done

echo ${alloc_list[@]}
