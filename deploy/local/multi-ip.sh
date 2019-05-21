#!/bin/bash
dev=wlp58s0
#dev=wlp2s0
base='172.1.1.'
postfix=100
end=163
i=0

dev_=`ip address show|grep $dev`
if [ "$dev_" = "" ]
then
#  dev=wlp2s0
  dev=eth0
fi

while [ "$postfix" -le "$end" ]
do
  ip="$base$postfix"
  ip address add $ip/255.255.255.0 dev $dev
  ((postfix=$postfix+1))
done

num=`ip address show $dev|grep "172.1.1.1"|wc -l`
echo "created $num ip's"
