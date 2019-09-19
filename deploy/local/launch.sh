#!/bin/bash
exe_consensus=$HOME/work/Logos/logos-core/build
db_consensus=./DB/Consensus_
db_txa_consensus=./DB/TXA/Consensus_
inst=32
clean="1"
runtest="0"
n_nodes=""
build="1"
micro_test="0"
base='172.1.1.'
postfix=100
end=131
restore="0"
templ="1"
txa=""
propagate="0"
p2p="--p2p"


n_started ()
{
  n_nodes=`ps -A|grep logos_core|wc -l`
}

n_started_print ()
{
  msg="$1"
  n_started
  echo "$msg $n_nodes"
}

ipconfig=`sudo ip address show | grep 172.1.1.100`
if [ "$ipconfig" = "" ]
then
  echo "####################################"
  echo "Creating multiple IP"
  sudo ./multi-ip.sh
fi

while [ "$1" != "" ]
do
  if [ "$1" = "--instances" ]
  then
    shift
    inst=$1
  elif [ "$1" = "--no-clean" ]
  then
    clean="0"
  elif [ "$1" = "--no-template" ]
  then
    templ="0"
  elif [ "$1" = "--restore" ]
  then
    restore="1"
  elif [ "$1" = "--test" ]
  then
    shift
    runtest="$1"
  elif [ "$1" = "--no-build" ]
  then
    build="0"
  elif [ "$1" = "--logos_core" ]
  then
    shift
    exe_consensus="$1"
  elif [ "$1" = "--micro-test" ]
  then
    micro_test="1"
  elif [ "$1" = "--tx-acceptor" ]
  then
    txa="$1"
  elif [ "$1" = "--no-propagate" ]
  then
    propagate="0"
  elif [ "$1" = "--no-p2p" ]
  then
    p2p=""
  else
    echo "invalid argument $1"
    exit
  fi
  shift
done

db=$db_consensus
db_txa=$db_txa_consensus
exe=$exe_consensus/logos_core
echo "####################################"
if [ "$build" = "1" ]
then
  echo "### building target $exe"
  rm -f err
  cur=`pwd`
  cd $exe_consensus
  rm -f logos_core
  (cmake -DBOOST_ROOT="/usr/local/boost" -DACTIVE_NETWORK="logos_test_network" -DCMAKE_BUILD_TYPE="Debug" \
      -G "Unix Makefiles" ..\
      && make logos_core -j4) >& err
  if [ ! -f "./logos_core" ]
  then
    echo "failed to build"
    cat err
    exit
  else
    cd $cur
    ls -l $exe
    date
  fi
else
  echo "### target $exe"
fi
echo "####################################"

killall -9 logos_core
sleep 1

if [ "$clean" = "1" ]
then
  rm -rf ${db}*
  rm -rf ${db_txa}*
  rm -rf .logos
  rm -f sndoff recvoff
fi

if [ "$templ" = "1" ]
then
  ./maketempl.sh --instances $inst $txa
fi

if [ "$restore" = "0" ]
then
  echo "### database will be initialized"
fi

i=0
rm -f ./nodes
firstpostfix=$postfix
while [ $i -lt $inst ]
do
  echo "$base$postfix" >> ./nodes
  mkdir -p ${db}${i}
  cp genlogos.json ${db}${i}/genlogos.json
  if [ "$restore" = "0" ]
  then
    dummy=""
  elif [ "$inst" = "1" ]
  then
    cp data400.ldb ${db}${i}/data.ldb
  elif [ "$inst" = "64" ]
  then
    cp data3200.ldb ${db}${i}/data.ldb
  else
    cp data${inst}00.ldb ${db}${i}/data.ldb
  fi
  
  cur=`pwd`
  if [ "$p2p" != "" ]
  then
    ((postfix1=$postfix+1))
    ((postfix4=$postfix+4))
    ((postfix16=$postfix+16))
    ((i1=$i+1))
    ((i4=$i+4))
    ((i16=$i+16))
    if [ "$i1" -ge "$inst" ]
    then
  	  ((postfix1=$postfix1-$inst))
    fi
    if [ "$i4" -ge "$inst" ]
    then
  	  ((postfix4=$postfix4-$inst))
    fi
    if [ "$i16" -ge "$inst" ]
    then
  	  ((postfix16=$postfix16-$inst))
    fi
    if [ "$i" = "111" ]
    then
				#gdb -batch -ex "run" -ex "bt full" --args
				$exe --daemon --data_path ${db}${i} --bind ${base}${postfix} \
				--debug net \
				--addnode ${base}${postfix1} \
				--addnode ${base}${postfix4} \
				--addnode ${base}${postfix16} &
				#2>&1 >${db}${i}/gdb.log &
    else
				$exe --daemon --data_path ${db}${i} --bind ${base}${postfix} \
         --debug net \
				 --addnode ${base}${postfix1} \
				 --addnode ${base}${postfix4} \
				 --addnode ${base}${postfix16} &
    fi

    if [ "$txa" != "" ]
    then
      $exe --tx_acceptor --data_path ${db_txa}${i} &
    fi

    ((i=$i1))
    ((postfix=$postfix1))
  else
    $exe --daemon --data_path ${db}${i} &

    if [ "$txa" != "" ]
    then
      $exe --tx_acceptor --data_path ${db_txa}${i} &
    fi

    ((i=$i+1))
    ((postfix=$postfix+1))
  fi

done

n_started_print "started nodes: "

if [ "$runtest" = "1" ]
then
  sleep 10
  ./test.sh $inst
  stored=`egrep -E "Stored 6000" ${db}*/log/*|wc -l`
  err=`egrep -E "Error, received|Error receiving|unknown|NULL" ${db}*/log/*`
  echo "###############################"
  if [ "$stored" != "$inst" ]
  then
    echo "THE TEST FAILED : stored blocks on $del out of $inst"
  elif [ "$err" != "" ]
  then
    echo "THERE ARE SOME ERRORS"
    echo $err
  else
    echo "THE TEST SUCCEEDED"
  fi

  n_started_print "running nodes: "
  echo "###############################"
fi

perl -e '
while(1) 
{
  $stored = `./grep stored | wc -l`;
  if ($stored != 32)
  {
    printf "%d\r", $stored;
    sleep(1);
  }
  else
  {
    exit(0);
  }
}'

rm -f nodes1

#if [[ "$inst" = "64" && "$propagate" = "1" ]]
#then
#  ./propagate.sh
#fi
