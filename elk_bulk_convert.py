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
  -? | --help	    Show this help
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
elkkey = "VVFZMUozNEJkWEFFOE85dS1McGM6NEdXVUVPQW1UTS1XeG9xcUNsWnNPUQ=="
cacert = ""
url = "https://duriez92.ddns.net:9200"
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
  if 'action' not in df.columns[1].lower():
    print ("ERROR Second column of input file is not 'action'")
    exit (1)
  if '_id' not in df.columns[2]:
    print ("ERROR Third column of input file is not '_id'")
    exit (1)

  total_line = df.shape[0]
  total_col = df.shape[1]
  if (verbose):
    print ("[DEBUG]Number of lines   = ", total_line)
    print ("[DEBUG]Number of columns = ", total_col)
    print ("-------------------------------------------")

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
  empty_action = False
  line = 0
  # We open the CSV file and we are going to read it line by line
  if (outfilename != '' ):
    outfile.write ('POST _bulk')
  
  while line < total_line:
    # For each line we build the bulk API line for ELK
    first_line = ""         # to define if it's an update, create or delete
    second_line = "{"       # to setup all the fields after _id not used for delete
    empty_action = False    # When action is not one of the 3 it won't be take into account
    # CREATE
    if ( df.iloc[line,1] == 'create' ):
      if ( df.iloc[line,2] == '' ):
        first_line = '\n{"create" : {"_index":"'+ str(df.iloc[line,0]) +'"}}'
      else:
        first_line = '\n{"create" : {"_index":"'+ str(df.iloc[line,0]) +'","_id":"'+ str(df.iloc[line,2]) +'"}}'
      second_line = '\n{'
      col = 3
      # Copy all remaining colums in the line
      while col < total_col:
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
      first_line = '\n{"update" : {"_index":"'+ str(df.iloc[line,0]) +'","_id":"'+ str(df.iloc[line,2]) +'"}}'
      second_line = '\n{"doc":{'
      col = 3
      # Copy all remaining colums in the line
      while col < total_col:
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
      first_line = '\n{"delete" : {"_index":"'+ str(df.iloc[line,0]) +'","_id":"'+ str(df.iloc[line,2]) +'"}}'
      second_line = ''
      if (outfilename != ''):
        outfile.write ( first_line )
      if (update):
        tmpfile.write( first_line)
    # OTHER
    else:
      # If action is emty or not equal to create, update or delete by default become update
      empty_action = True
      first_line = '\n{"update" : {"_index":"'+ str(df.iloc[line,0]) +'","_id":"'+ str(df.iloc[line,2]) +'"}}'
      second_line = '\n{ "doc" : {'
      col = 3
      # Copy all remaining colums in the line
      while col < total_col:
        second_line = second_line + '"'+ str(df.columns[col]) +'":"'+ str(df.iloc[line,col])+ '",'
        col+=1
      # At the end we remove the last ',' and put '}'
      size = len(second_line)
      second_line = second_line[:size - 1] + '} }'
      if (update):
        tmpfile.write( first_line)
        tmpfile.write( second_line)     
    line+=1
  
  if (outfilename != '' ):
    outfile.write("\n")
    outfile.close()
  
  # ELK update step
  if (update):
    tmpfile.write("\n")
    tmpfile.close()
    cmdline = 'curl -k -s --cacert ' + cacert + ' -H "Authorization: ApiKey ' + elkkey + '" -H "Content-Type: application/json" -X POST "'+ url +'/_bulk?pretty" --data-binary "@'+tmpfilename+'" > curl.out'
    if (verbose):
      print ("[DEBUG] ", cmdline)
      print ("-------------------------------------------")
    # Run of a curl command line with the bulk API. JSON ELK answer will be store into file curl.out
    os.system(cmdline)
    # Open API respons in curl.out file
    curlout = open('curl.out')
    # We load the ELK JSON answer of the bulk API request
    curl_data = json.load(curlout)
    # Test if command failed
    
    # i is the CSV or Excel file line number
    i = 0
    # we read the JSON output answer to update _id if needed
    for rec in curl_data['items']:
      recaction = list(rec)[0]
      if ( recaction == "create" or recaction == "update" ):
        # Check if error encountered
        if ( str(rec[recaction]['status']) != "201" ):
          print ('[ERROR-'+str(rec[recaction]['status'])+'] line '+ str(i+2) +' - _id: '+ str(rec[recaction]['_id'])+' Check if \ or \\\ - ('+ str(rec[recaction]['error']['caused_by']['reason'])+')')
          df.loc[i,'action'] = "ERROR"
          df.loc[i,'_id'] = rec[recaction]['_id']
        else:
          # After execution, the action is moved to empty in the CSV file
          df.loc[i,'action'] = ""
          df.loc[i,'_id'] = rec[recaction]['_id']
      i+=1
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
      print ("-------------------------------------------")
    else:
      os.remove("curl.out")
      os.remove(tmpfilename)
        

##########################################################
## Program
if __name__ == "__main__":
  main(sys.argv[1:])
######################### END ############################