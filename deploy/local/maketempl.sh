#!/bin/bash
del=0
end=15
baseip="172.1.1."
postfix="100"
postfix_="$postfix"
port=7075
p2p=""
db="DB"
config="config.json.templ"
txa="0"

while [ "$1" != "" ]
do
  if [ "$1" = "--instances" ]
  then
    shift
    end=$1
  elif [ "$1" = "--tx-acceptor" ]
  then
    txa="1"
  elif [ "$1" = "--p2p" ]
  then
    p2p="1"
  fi
  shift
done

enddel=$end

#if [[ "$enddel" -gt "32" && "$p2p" != "" ]]
#then
#    enddel=32
#fi

while [ "$del" -lt "$end" ]
do
  mkdir -p $db/Consensus_$del
  mkdir -p $db/TXA/Consensus_$del
  cat $config | perl -e '
    $baseip = "'$baseip'";
    $postfix = '$postfix';
    $postfix_ = '$postfix_';
    $delegate_id = '$del';
    $port = '$port';
    $end = '$end';
	$enddel = '$enddel';
    $txa = '$txa';
    $local_ip = $baseip . $postfix;
    while ($line = <>)
    {
      chomp $line;
      $line =~ s/LOCAL_IP/$local_ip/;
      $line =~ s/DELEGATE_ID/$delegate_id/;
      $line =~ s/PEERING_PORT/$port/;
      $line =~ s/TXA_DEL_IP/$local_ip/;
      $line =~ s/TXA_IP/$local_ip/;
      printf "%s\n", $line;
      if ($line =~ /delegate_peers/)
      {
        for ($del = 0; $del < $enddel; $del++)
        {
          $ip = $baseip . ($postfix_ + $del);
          printf "\t\t\t{\n";
          printf "\t\t\t\t\"ip_address\": \"%s\",\n", $ip;
          printf "\t\t\t\t\"delegate_id\": \"%s\"\n", $del;
          printf "\t\t\t}%s\n", ($del != $enddel-1) ? "," : "";
        }
      }
      if ($txa ne "0")
      {
        if ($line =~ /tx_acceptors/)
        {
          printf "\t\t\t{\n";
          printf "\t\t\t\t\"ip\": \"%s\",\n", $local_ip;
          printf "\t\t\t\t\"port\": \"56000\"\n";
          printf "\t\t\t}\n";
        }
      }
    }
  ' > $db/Consensus_$del/config.json

  #   "tx_acceptors":[
	#	{
	#		"ip": "172.1.1.100",
	#		"port": "56000"
	#	}
  cat $db/Consensus_$del/config.json | perl -e '
    $skip = 0;
    while(<>) {
      if ($skip == 0) {
        print $_;
      }
      if (/tx_acceptors/) {
        $skip = 1;
      } elsif (/\}/) {
        $skip = 0;
      }
    }
  ' > $db/TXA/Consensus_$del/config.json

  ((postfix=$postfix+1))
  ((del=$del+1))
  ((port=$port+1))
done
