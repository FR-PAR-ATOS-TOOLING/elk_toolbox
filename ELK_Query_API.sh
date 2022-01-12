#!/bin/sh
##################################################
#
# Program : ELK_Query_API.sh
# Date : 01/2022
# Author : A. Duriez
#
##################################################

#set -x # => for DEBUG
#---------------------- Function ------------------------------------
help(){
  printf "\n---------------------------------------------------------"
  printf "\nPurpose :"
  printf "\n  This script is use to execute an API ELK request"
  printf "\n  An ELK query is requested via GET [index]-*/_search in the DEV TOOL Console of Kibana."
  printf "\nInput :"
  printf "\n  -c ca_file.crt = Kibana Root Authority certificat file [Mandatory]"
  printf "\n  -q file.curl = ELK query file able to be used as curl file data [Mandatory]"
  printf "\n  -o file.json = name of output file to store API result [Mandatory]"
  printf "\n  -u "URL" = URL of target ELK Node (ie https://localhost:9200/) [Mandatory]"
  printf "\n  -k "hdffqhhj" = API key to allow Kibana access [Mandatory]"
  printf "\n  -z = To force the gzip of the result file"
  printf "\n  -m mail.in = a file used to send a mail at least in the file we should have:"
  printf "\n    to: <email 1> <email 2>"
  printf "\n    subject: \"to update with expected\""
  printf "\n    from: <email like no-reply-elk@customer.fr>"
  printf "\n  -v = Add Verbose information"
  printf "\n  -h = This Help"
  printf "\nExemple:"
  printf "\n./ELK_Query_API.sh \\"
  printf "\n-q ./cpu_type.curl \\"
  printf "\n-c ./ca.crt \\"
  printf "\n-o ./cpu_type.json \\"
  printf "\n-k VVFZMUozNEJkWEFFOE85dS1McGM6NEdXVUVPQW1UTS1XeG9xcUNsWnNPUQ== \\"
  printf "\n-u \"https://duriez92.ddns.net:9200/threshold/_search\" \\"
  printf "\n-v"
  printf "\n---------------------------------------------------------"
  printf "\n\n"
  exit
}
#------------------ Global Variables --------------------------------
QUERYFILE=""
OUTPUTFILE=""
URL="https://duriez92.ddns.net:9200/threshold/_search"
APIKEY="VVFZMUozNEJkWEFFOE85dS1McGM6NEdXVUVPQW1UTS1XeG9xcUNsWnNPUQ=="
MAILFILE=""
CAFILE=""
DEBUG=false
HELP=false
ZIPFILE=false
#------------------------ Main --------------------------------------
# Get inputs from cmd line
while getopts 'c:q:o:u:k:m:vhz' c
 do
  case $c in
    c) CAFILE=$OPTARG ;;
    q) QUERYFILE=$OPTARG ;;
    o) OUTPUTFILE=$OPTARG ;;
    u) URL=$OPTARG ;;
    k) APIKEY=$OPTARG ;;
    m) MAILFILE=$OPTARG ;;
    v) DEBUG=true ;;
    h) HELP=true ;;
    z) ZIPFILE=true ;;
  esac
 done

if [ $DEBUG = true ]
  then
    printf "\n----------------------------------------------------"
    printf "\n[DEBUG] Start - `date`"
    printf "\n[DEBUG] [Mandatory] CAFILE=$CAFILE"
    printf "\n[DEBUG] [Mandatory] QUERYFILE=$QUERYFILE"
    printf "\n[DEBUG] [Mandatory] OUTPUTFILE=$OUTPUTFILE"
    printf "\n[DEBUG] [Mandatory] URL=$URL"
    printf "\n[DEBUG] [Mandatory] APIKEY=$APIKEY"
    printf "\n[DEBUG] MAILFILE=$MAILFILE"
    printf "\n[DEBUG] ZIPFILE=$ZIPFILE"
    printf "\n----------------------------------------------------"
  fi
if [ $HELP = true ]
  then
    help
  fi

# Test parameter 
if [ "$CAFILE" = "" -o "$QUERYFILE" = "" -o "$OUTPUTFILE" = "" -o "$URL" = "" -o "$APIKEY" = "" ]
  then
    printf "\n----------------------------------------------------"
    printf "\nERROR - Parameter is missing"
    help
  fi

# Cut URL to have ELK node and ELK index
INDEX=`echo $URL | awk -F / '{print $4}'`
TARGET=`echo $URL | awk -F / '{print $3}'`
rm -f $OUTPUTFILE
# Get the number of record to extract
NBR_REC=`curl -k -s --cacert $CAFILE -H "Authorization: ApiKey $APIKEY" -H 'Content-Type: application/json' -XPOST "https://$TARGET/$INDEX/_count" --data "@$QUERYFILE" | jq .count`
if [ $DEBUG = true ]
  then
	printf "\n[DEBUG] ELK TARGET=$TARGET"
	printf "\n[DEBUG] ELK INDEX=$INDEX"
	printf "\n[DEBUG] curl -k --cacert $CAFILE -H \"Authorization: ApiKey $APIKEY\" -H 'Content-Type: application/json' -XPOST \"https://$TARGET/$INDEX/_count\" --data \"@$QUERYFILE\" | jq .count"
    printf "\n[DEBUG] Number of target record: $NBR_REC"
    printf "\n----------------------------------------------------"
  fi

if [ $NBR_REC -gt 5000 ]
  then
  # Setup LOOP_VAR = number of iteration of 5000 records to do
  LOOP_VAR=$((($NBR_REC/5000)+1))
  if [ $DEBUG = true ]
    then
	  printf "\n[DEBUG] LOOP_VAR=$LOOP_VAR"
      printf "\n----------------------------------------------------"
	fi
  # Creation of a Point In Time (PIT) ID
  PIT=`curl -k -s --cacert $CAFILE -H "Authorization: ApiKey $APIKEY" -H 'Content-Type: application/json' -XPOST "https://$TARGET/$INDEX/_pit?keep_alive=5m" | jq .id`
  if [ $DEBUG = true ]
    then
	  printf "\ncurl -k --cacert $CAFILE -H \"Authorization: ApiKey $APIKEY\" -H 'Content-Type: application/json' -XPOST \"https://$TARGET/$INDEX/_pit?keep_alive=5m\" | jq .id"
	  printf "\n[DEBUG] PIT=$PIT"
      printf "\n----------------------------------------------------"
	fi
  printf '{"size": 5000,"pit": {"id" : '$PIT',"keep_alive": "5m"},"sort": [{"_id": {"order": "desc","unmapped_type": "boolean"}}],' > pit.curl
  cat $QUERYFILE | jq -c . | sed -e 's/^{//' >> pit.curl
  
  #Retreive block of 5000 records
  if [ $DEBUG = true ]
    then
      printf "\ncurl -k --cacert $CAFILE -H \"Authorization: ApiKey $APIKEY\" -H 'Content-Type: application/json' -XPOST \"https://$TARGET/_search\" --data \"@pit.curl\"| jq .hits.hits > tmpfile.json"
      printf "\n----------------------------------------------------"
    fi
  curl -k -s --cacert $CAFILE -H "Authorization: ApiKey $APIKEY" -H 'Content-Type: application/json' -XPOST "https://$TARGET/_search" --data "@pit.curl" | jq .hits.hits > tmpfile.json 
  # Remove last '}' and ']' from output file 
  head -n -2 tmpfile.json >> $OUTPUTFILE
  # Adding '},' to continue JSON list
  echo "  }," >> $OUTPUTFILE
  tail -n +2 tmpfile.json >> $OUTPUTFILE
  cat pit.curl | jq -c '. |= . + {"search_after": [ "youpi", 12587 ] }' > newpit.curl
  mv newpit.curl pit.curl
  
  #Closing session of PIT ID
  RET=`curl -k -s --cacert $CAFILE -H "Authorization: ApiKey $APIKEY" -H 'Content-Type: application/json' -XDELETE "https://$TARGET/_pit" -d '{"id": '$PIT' }'`
  if [ $DEBUG = true ]
    then
	  printf "\ncurl -k --cacert $CAFILE -H \"Authorization: ApiKey $APIKEY\" -H 'Content-Type: application/json' -XDELETE \"https://$TARGET/_pit\" -d '{\"id\":$PIT}'"
      printf "\n[DEBUG] PIT delete : $RET"
      printf "\n----------------------------------------------------"
    fi
  else
  # Execute curl cmd to target ELK node
  if [ $DEBUG = true ]
    then
      printf "\n[DEBUG] curl -k --cacert $CAFILE -H \"Authorization: ApiKey $APIKEY\" -o $OUTPUTFILE -H 'Content-Type: application/json' -XPOST \"$URL\" --data \"@$QUERYFILE\"\n"
    fi
  curl -k -s --cacert $CAFILE -H "Authorization: ApiKey $APIKEY" -o $OUTPUTFILE -H 'Content-Type: application/json' -XPOST "$URL" --data "@$QUERYFILE"

  # If zip requested, file is created
  if [ $ZIPFILE = true ]
    then
      /usr/bin/gzip $OUTPUTFILE
      OUTPUTFILE=$OUTPUTFILE.gz
    fi

  # If mail is requested, mail is sent
  if [ ! -z "$MAILFILE" ]
    then
      SUBJECT=`cat $MAILFILE | grep "^subject" | cut -d: -f 2 | sed 's/"//g' | sed 's/^ //'`
      FROMUSER=`cat $MAILFILE | grep "^from" | cut -d: -f 2 | sed 's/"//g' | sed 's/^ //'`
      TO_USER=`cat $MAILFILE | grep "^to" | cut -d: -f 2 | sed 's/"//g' | sed 's/^ //'`
      if [ $DEBUG = true ]
        then
          printf "\n[DEBUG] mail -s \"$SUBJECT\" -r \"$FROMUSER\" -a $OUTPUTFILE $TO_USER\n"
        fi
      echo "" | /usr/bin/mail -s "$SUBJECT" -r "$FROMUSER" -a $OUTPUTFILE $TO_USER
    fi
fi
if [ $DEBUG = true ]
  then
    printf "\n----------------------------------------------------"
    printf "\n[DEBUG] End - `date`"
    printf "\n----------------------------------------------------"
    printf "\n"
  fi
#------------------------ End ---------------------------------------
