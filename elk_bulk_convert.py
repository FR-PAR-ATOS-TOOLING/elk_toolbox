######################### START ###########################
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Goal : Convert an Excel or a CSV file into a file usable with ELK Dev Tools
Usage: python elk_bulk_convert.py [Options]
       CSV file must be:
        - First line = header with mandatory fields: index, action and _id in this order
        - First column "index" = ELK index to update
        - Second column "action" = action: create, update, delete or empty
                          if empty and -u is selected the line will become 'update'
        - Third column "_id" = ELK doc id mandatory for update, delete or empty

Options:
  -? | --help       Show this help
  -v | --verbose    Print to output some messages for debuging
  -f | --infile     Input file name .csv (; separator) or .xlsx - Mandatory
  -o | --outfile    Output file for drag and drop in DEV ELK, if empty output is Console
  -u | --update     Update the ELK index in the cluster node
  -c | --cacert     ca.crt file for https ELK access [Mandatory if -u]
  -k | --key        ELK API key with write role on target index [Mandatory if -u]
  -t | --url        ELK url like https://localhost:9200 [Mandatory if -u]

Exemple:
python elk_bulk_convert.py -f "C:\\temp\\file.csv" -v -o out.out -u -k tyyvhbkjvhcgchfc -t https://localhost:9200 -c ca.crt
"""

###########################################################
# Import section

import os
import os.path
import glob
import sys
from datetime import datetime
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
verbose = 0                                # 1 for debugging mode
infilename = "test.csv"    # CSV file with ';' separator
outfilename = ""           # File with he bulk api command line to past and cut to ELK Dev Tool
update = 0                 # 1 for update ELK index
elkkey = "" # API infra test
cacert = ""
url = "" # URL infra test
outfile = ""
CSVFILE = 0
EXCELFILE = 0
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

##########################################################
## Function main
def main(argv):
  inputvar(argv)
  dirfile,var = os.path.split(infilename)
  now = datetime.now()
  if (verbose):
    print ("\n------------------ START : ",str(now.strftime("%d/%m/%Y %H:%M:%S"))," ----------------------------")
    print ("[DEBUG]file in \t= ", infilename)
    print ("[DEBUG]file out = ", outfilename)
    print ("[DEBUG]directory = ", dirfile)
    print ("[DEBUG]update = ", update)
    print ("[DEBUG]url = ", url)
    print ("[DEBUG]key = ",elkkey)
    print ("[DEBUG]ca.crt file = ", cacert)
    print ("-----------------------------------------------------------------------------")

  # Check input file be compliant
  if ".csv" in infilename:
    # Open CSV file and store it inside a dataframe panda structure
    df = pd.read_csv(infilename, sep=';', keep_default_na=False)
  elif ".xlsx" in infilename:
    # Open Excel file and store it inside a dataframe panda structure
    df = pd.read_excel(infilename, keep_default_na=False)
  else:
    print ("ERROR Input file must be .csv or .xlsx")
    exit (1)

  # Check required column name and order
  if 'index' not in df.columns[0].lower():
    print ("ERROR First column of input file is not 'index'")
    exit (1)
  if 'action' not in df.columns[1]:
    print ("ERROR Second column of input file is not 'action'")
    exit (1)
  if '_id' not in df.columns[2]:
    print ("ERROR Third column of input file is not '_id'")
    exit (1)

  total_line = df.shape[0]
  total_col = df.shape[1]
  if (verbose):
    print ("[DEBUG]Number of lines   = ", total_line+1 )
    print ("[DEBUG]Number of columns = ", total_col+1 )
    print ("-----------------------------------------------------------------------------")

  # Setup the output file if requested
  if ( outfilename != '' ):
    outfile = open (outfilename,'w')

  if (update):
    # tmpfile is used to store the curl data for ELK update
    tmpfilename = infilename + ".tmp"
    tmpfile = open (tmpfilename,'w')
    if ( cacert == ""):
      print ("ERROR missing parameter for ELK update")
      exit (1)
  line = 0
  nbr_update = 0 # Number of records created, updated or deleted
  # We open the CSV file and we are going to read it line by line
  if (outfilename != '' ):
    outfile.write ('POST _bulk')
  
  while line < total_line:
    # For each line we build the bulk API line for ELK
    first_line = ""         # to define if it's an update, create or delete
    second_line = "{"       # to setup all the fields after _id not used for delete
    # CREATE
    if ( df.iloc[line,1] == 'create' ):
      nbr_update+=1
      if ( df.iloc[line,2] == '' ):
        first_line = '\n{"create" : {"_index":"'+ str(df.iloc[line,0]) +'"}}'
      else:
        first_line = '\n{"create" : {"_index":"'+ str(df.iloc[line,0]) +'","_id":"'+ str(df.iloc[line,2]) +'"}}'
      second_line = '\n{'
      col = 3
      # Copy all remaining colums in the line
      while col < total_col:
        if not str(df.iloc[line,col]):
          second_line = second_line + '"'+ str(df.columns[col]) +'":"'+ str(df.iloc[line,col])+ '",'
        elif ( str(df.iloc[line,col])[0].isdigit() ):
          second_line = second_line + '"'+ str(df.columns[col]) +'":'+ str(df.iloc[line,col])+ ','
        else:
          second_line = second_line + '"'+ str(df.columns[col]) +'":"'+ str(df.iloc[line,col])+ '",'
        col+=1
      # At the end we remove the last ',' and put '}'
      size = len(second_line)
      second_line = second_line[:size - 1] + '}'
      if (outfilename != ''):
        outfile.write ( first_line )
        outfile.write ( second_line )
      if (update):
        tmpfile.write( first_line)
        tmpfile.write( second_line)
    # UPDATE
    elif ( df.iloc[line,1] == 'update' ):
      nbr_update+=1
      first_line = '\n{"update" : {"_index":"'+ str(df.iloc[line,0]) +'","_id":"'+ str(df.iloc[line,2]) +'"}}'
      second_line = '\n{"doc":{'
      col = 3
      # Copy all remaining colums in the line
      while col < total_col:
        if not str(df.iloc[line,col]):
          second_line = second_line + '"'+ str(df.columns[col]) +'":"'+ str(df.iloc[line,col])+ '",'
        elif ( str(df.iloc[line,col])[0].isdigit() ):
          second_line = second_line + '"'+ str(df.columns[col]) +'":'+ str(df.iloc[line,col])+ ','
        else:
          second_line = second_line + '"'+ str(df.columns[col]) +'":"'+ str(df.iloc[line,col])+ '",'
        col+=1
      # At the end we remove the last ',' and put '}'
      size = len(second_line)
      second_line = second_line[:size - 1] + '} }'
      if (outfilename != ''):
         outfile.write ( first_line )
         outfile.write ( second_line )
      if (update):
        tmpfile.write( first_line)
        tmpfile.write( second_line)
    # DELETE
    elif ( df.iloc[line,1] == 'delete' ):
      nbr_update+=1
      first_line = '\n{"delete" : {"_index":"'+ str(df.iloc[line,0]) +'","_id":"'+ str(df.iloc[line,2]) +'"}}'
      second_line = ''
      if (outfilename != ''):
        outfile.write ( first_line )
      if (update):
        tmpfile.write( first_line)
    line+=1

  if (verbose):
    print ("[DEBUG] Update requested (create/update/delete): ", nbr_update)
    print ("-----------------------------------------------------------------------------")

  if (outfilename != '' ):
    outfile.write("\n")
    outfile.close()

  # ELK update step and modification of the Darafram to reflect API return JSON
  if (update and nbr_update != 0):
    tmpfile.write("\n")
    tmpfile.close()
    cmdline = 'curl -k -s --cacert ' + cacert + ' -H "Authorization: ApiKey ' + elkkey + '" -H "Content-Type: application/json" -X POST "'+ url +'/_bulk?pretty" --data-binary "@'+tmpfilename+'" > curl.out'
    if (verbose):
      print ("[DEBUG] ", cmdline)
      print ("-----------------------------------------------------------------------------")
    # Run of a curl command line with the bulk API. JSON ELK answer will be store into file curl.out
    os.system(cmdline)
    # Open API respons in curl.out file
    curlout = open('curl.out')
    # We load the ELK JSON answer of the bulk API request
    curl_data = json.load(curlout)
    # Test if error encoutered
    if ( 'error' in curl_data):
      curlout.close()
      errorfile = open (infilename+'.errlog','a')
      print ("[ERROR - "+str(now.strftime("%d/%m/%Y %H:%M:%S"))+"] "+str(curl_data['error']))
      print ("[ERROR - "+str(now.strftime("%d/%m/%Y %H:%M:%S"))+"] "+str(curl_data['error']), file=errorfile)
      os.remove("curl.out")
      os.remove(tmpfilename)
      errorfile.close()
      exit(1)
    # Setup a list with line in the csv where creation is requested without given an _id (let ELK give it in API respond)
    empty_create_list = df.loc[((df['action'] == "create") & (df['_id'] == ""))].index.tolist() 
    # we read the ELK API respond to update _id and set action to empty 
    for rec in curl_data['items']:
      rec_action = list(rec)[0]  # Get action from ELK API
      rec_id = str(rec[rec_action]['_id'])  # Get ELK record _id from API respond
      if ( rec_action == "create" or rec_action == "update" ):
        # Check if error encountered
        if ( str(rec[rec_action]['status']) != "201" and str(rec[rec_action]['status']) != "200" ):
          df.loc[(df['_id'] == rec_id),'action'] = "ERROR"
          print ("[API ELK ERROR - "+str(now.strftime("%d/%m/%Y %H:%M:%S"))+"] status: "+str(rec[rec_action]['status'])+" - "+str(rec) )
        else:
          # Check if _id is known in the dataframe (csv or excel input file)
          if str(rec_id) in df['_id'].values :
            # Empty action field in dataframe because executed by ELK
            df.loc[(df['_id'] == rec_id),'action'] = ""
          else:
            # For create only, if _id not find in dataframe we take the first create line and set the ELK _id
            df.loc[empty_create_list[0], '_id'] = rec_id
            # Now _id is setup in Dataframe and action can be erased because it was executed
            df.loc[(df['_id'] == rec_id),'action'] = ""
            if len(empty_create_list) > 1:
              empty_create_list.pop(0)  # we removed the first line of updated line without _id in the dataframe
    
    # At the end we remove all deleted line from the DataFrame
    indextodrop = df[ df['action'] == "delete"].index
    df.drop(indextodrop, inplace=True)
    
    # DataFrame is stored in a temporary CSV file named output.csv
    if os.path.exists(infilename + '.bkp'):
      os.remove(infilename + '.bkp')
    os.rename(infilename,infilename + '.bkp')
    if ".csv" in infilename:
      # Open CSV file and store it inside a dataframe panda structure
      df.to_csv(infilename, index=False, sep=';')
    elif ".xlsx" in infilename:
      # Open Excel file and store it inside a dataframe panda structure
      df.to_excel(infilename, index=False)
    curlout.close()
    # Initial CSV file is replaced by the new one updated with _id or wit deleted lines removed
    if (verbose):
      print ("[DEBUG] Update initial file" , infilename, " after ELK bulk update" )
      print ("[DEBUG] files curl.out and ", tmpfilename , " not deleted")
    else:
      os.remove("curl.out")
      os.remove(tmpfilename)
  if (verbose):
    print ("------------------- END: ",str(now.strftime("%d/%m/%Y %H:%M:%S")),"  -----------------------------")


##########################################################
## Program
if __name__ == "__main__":
  main(sys.argv[1:])
######################### END ############################

