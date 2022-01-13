######################### START ###########################
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Goal : Convert a CSV file into a file usable with ELK Dev Tools  
Usage: python elk_bulk_convert_csv.py [Options]
       CSV file must be:
        - First line = header with fields to add
        - First column = ELK index to update
        - Second column = action: create, update, delete or empty
                          if empty and -u is selected the line will become 'update'
        - Third column = ELK doc id mandatory for update, delete or empty

Options:
  -? | --help	    Show this help
  -v | --verbose    Print to output some messages for debuging
  -f | --infile     Input csv file name - Mandatory
  -o | --outfile    Output file for drag and drop in DEV ELK, if empty output is Console
  -u | --update     Update the ELK index in the cluster node
  -c | --cacert     ca.crt file for https ELK access [Mandatory if -u]
  -k | --key        ELK API key with write role on target index [Mandatory if -u]
  -t | --url        ELK url like https://localhost:9200 [Mandatory if -u]

Exemple:
python elk_bulk_convert_csv.py -f "C:\\temp\\file.csv" -v -o out.out -u -k tyyvhbkjvhcgchfc -t https://localhost:9200 -c ca.crt
"""

###########################################################
# Import section

import os
import os.path
import glob
import sys
import getopt
import string
import shutil
import fileinput
import requests
import json
import csv
import pandas as pd

###########################################################
# Global Variables
verbose = 0				   # 1 for debugging mode
infilename = "test.csv"    # CSV file with ';' separator
outfilename = ""           # File with he bulk api command line to past and cut to ELK Dev Tool
update = 0                 # 1 for update ELK index
elkkey = ""
cacert = ""
url = ""
outfile = ""
###########################################################
# Def section - function

## Function which call the comment for usage at the beginning
def usage():
  print ( __doc__ )

def inputvar(argv):
  try:
  # To update with all possible arguments
    opts, args = getopt.getopt(argv, "?vf:o:uc:k:t:", ["help","verbose","infile=","outfile=","update","cacert","key","url"]) # see getopt python doc
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  # Check command line arguments and affect variables
  for opt, arg in opts:
    if opt in ("-?","--help"):
      usage()
      sys.exit()
    elif opt in ("-v","--verbose"):
      global verbose
      verbose = 1
    elif opt in ("-f","--infile"):
      global infilename
      infilename = arg
    elif opt in ("-o","--outfile"):
      global outfilename
      outfilename = arg
    elif opt in ("-u","--update"):
      global update
      update = 1
    elif opt in ("-t","--url"):
      global url
      url = arg
    elif opt in ("-k","--key"):
      global elkkey
      elkkey = arg
    elif opt in ("-c","--cacert"):
      global cacert
      cacert = arg
      
  if (verbose):
    print ("------------------ START ------------------")
    print ("[DEBUG]file in \t= ", infilename)
    print ("[DEBUG]file out = ", outfilename)
    print ("[DEBUG]update = ", update)
    print ("[DEBUG]url = ", url)
    print ("[DEBUG]key = ",elkkey)
    print ("[DEBUG]ca.crt file = ", cacert)
    print ("-------------------------------------------")

##########################################################
## Function main
def main(argv):
  inputvar(argv)
  if ( outfilename != '' ):
    outfile = open (outfilename,'w')
  if (update):
    # tmpfile is used to store the curl data for ELK update
    tmpfilename = infilename + ".tmp"
    tmpfile = open (tmpfilename,'w')
    if ( cacert == ""):
      print ("ERROR missing parameter for ELK update")
      exit (1)
  empty_action = False
  line = 0
  # We open the CSV file and we are going to read it line by line
  with open(infilename, newline='') as infile:
    reader = csv.reader(infile, delimiter=';')
    if (outfilename != '' ):
      outfile.write ('POST _bulk\n')
    for row in reader:
      if (line == 0 ):
      # First line of CSV file is the columns name
        firstline = row
      else:
      # We read each line colums by colums to create the bulk line
        i = 0
        tmpline = "{"
        actionline = ""   # actionline is used to define if it's an update, create or delete
        for col in row:
          if ( i == 0 ):
          # ELK target index must be the first column
            elk_index = col
          elif ( i == 1 ):
           # ELK action must be the second column and must be create, delete or update. If empty = update
           elk_action = col
          elif ( i == 2 ):
            elk_id = col
            if ( elk_action == '' ):
              elk_action = 'update'
              empty_action = True              
            if ( elk_action == 'delete' or elk_action == 'update'):
            # For delete or update, id on the ELK record is mandatory in colums 3
              actionline = '{"'+ elk_action +'":{"_index":"'+ elk_index +'","_id":"'+ elk_id +'"}}'
              if ( elk_id == "" ):
                print ("ERROR - Line ", line + 1, " of ", infilename, " ELK id is not empty")
                exit (1)
            else:
            # For create action id could be empty or defined, if empty it will be added by ELK during creation
              if ( elk_id == "" ): 
                actionline = '{"create":{"_index":"'+ elk_index +'"}}'
              else:
                actionline = '{"create":{"_index":"'+ elk_index +'","_id":"'+ elk_id +'"}}'              
          else:
          # For update or create, we put a second line of data require by the ELK Bulk API
            tmpline = tmpline + "\"" + firstline[i] + "\":\"" + col + "\","
          i+=1
        txt = actionline + '\n'
        if (outfilename != '' and not empty_action):
          outfile.write ( txt )
        if (update):
          tmpfile.write( txt )
        if ( elk_action == 'create' or elk_action == 'update'):
        # Only for create and update action we create the second line of bulk API
          size = len(tmpline)
          outline = tmpline[:size - 1]
          if ( elk_action == 'create'):
            txt = outline + '}\n'
            if (outfilename != '' ):
              outfile.write ( txt )
            if (update):
              tmpfile.write( txt )
          else:
          # For update a special syntax is required at the begining
            txt = '{ "doc" : ' + outline +'} }\n' 
            if (outfilename != '' and not empty_action):
              outfile.write ( txt )
            if (update):
              tmpfile.write( txt)
            empty_action = False
      line+=1
  
  if (outfilename != '' ):
    outfile.close()
  if (update):
    tmpfile.close()
    cmdline = 'curl -k -s --cacert ' + cacert + ' -H "Authorization: ApiKey ' + elkkey + '" -H "Content-Type: application/json" -X POST "'+ url +'/_bulk?pretty" --data-binary "@'+tmpfilename+'" > curl.out'
    if (verbose):
      print ("[DEBUG] ", cmdline)
      print ("-------------------------------------------")
    # Run of a curl command line with the bulk API. JSON ELK answer will be store into file curl.out
    os.system(cmdline)
    curlout = open('curl.out')
    # We load the ELK JSON answer of the bulk API request
    data = json.load(curlout)
    # We open the CSV file and load it inside a Panda DataFrame structure in memory
    df = pd.read_csv(infilename, sep=';')
    # i is the CSV line
    i = 0
    # we read the JSON output answer to update _id if needed
    for rec in data['items']:
      recaction = list(rec)[0]
      if ( recaction == "create" or recaction == "update" ):
        #print (recaction + ' => ' + rec[recaction]['_id'] + ' - line: ' + str(i) + ' / seq ' + str(rec[recaction]['_seq_no']))
        # After execution, the action is moved to empty in the CSV file
        df.loc[i,'action'] = ""
        df.loc[i,'_id'] = rec[recaction]['_id']
      i+=1
    # At the end we remove all deleted line from the DataFrame
    indextodrop = df[ df['action'] == "delete"].index
    df.drop(indextodrop, inplace=True)
    # DataFrame is stored in a temporary CSV file named output.csv
    df.to_csv("output.csv", index=False, sep=';')
    curlout.close()
    os.remove("curl.out")
    os.remove(tmpfilename)
    infile.close()
    os.remove(infilename)
    # Initial CSV file is replaced by the new one updated with _id or wit deleted lines removed
    os.rename("output.csv", infilename)
    if (verbose):
      print ("[DEBUG] Update initial file" , infilename, " after ELK bulk update" )
      print ("-------------------------------------------")
        

##########################################################
## Program
if __name__ == "__main__":
  main(sys.argv[1:])
######################### END ############################
