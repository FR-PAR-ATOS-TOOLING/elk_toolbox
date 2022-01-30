#!/bin/sh
#####################################################################
#
# Program : ELK_Query_API_v2.sh
# Date : 01/2022
# Author : A. Duriez
#
#####################################################################

#------------------ Global Variables --------------------------------
DIR_INDEX="/data/github/elk_index_mgmt"

#------------------------ Main --------------------------------------
cd $DIR_INDEX
printf "[`date`] Start ----------------------------------------------\n"
git pull
printf "[`date`] File check -----------------------------------------\n"
for FIC in `find . -mmin -5 | grep "\.xlsx$\|\.csv$" | cut -d/ -f2`
do
  printf "[`date`] - File $FIC\n"
  /usr/local/bin/python3 /data/github/elk_toolbox/elk_bulk_convert.py -f $DIR_INDEX/$FIC -k VVFZMUozNEJkWEFFOE85dS1McGM6NEdXVUVPQW1UTS1XeG9xcUNsWnNPUQ== -t "https://duriez92.ddns.net:9200" -c /etc/elasticsearch/certs/ca.crt -u 
done

printf "[`date`] Git push ------------------------------------------\n"
git commit -a -m "Update `date "+%Y/%m/%d_%Hh%Mm%Ss"`"
git add .
git push

