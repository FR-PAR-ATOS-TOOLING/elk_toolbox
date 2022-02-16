#!/bin/sh
#####################################################################
#
# Program : ELK_Query_API_v2.sh
# Date : 01/2022
# Author : A. Duriez
#
#####################################################################

#------------------ Global Variables --------------------------------
DIR_INDEX="DIRECTORY_SYNCHRO_WITH_GIT"
APIKEY="API_KEY_TO_THE_TARGET_INDEX"
ELKSRV="NODE_OF-THE_ELK_CLUSTER"

#------------------------ Main --------------------------------------
cd $DIR_INDEX
printf "[`date`] Start ----------------------------------------------\n"
git pull
printf "[`date`] File check -----------------------------------------\n"
for FIC in `find . -mmin -5 | grep "\.xlsx$\|\.csv$" | cut -d/ -f2`
do
  printf "[`date`] - File $FIC\n"
  /usr/bin/python3 /data/atos_gitlab/elk_bulk_convert.py -f $DIR_INDEX/$FIC -k $APIKEY -t "https://$ELKSRV:9200" -c $DIR_INDEX/../ca-nephos.crt -u -v
  sleep 2
done

printf "[`date`] Git push ------------------------------------------\n"
git commit -a -m "Update `date "+%Y/%m/%d_%Hh%Mm%Ss"`"
git add .
git push

