######################### START ###########################
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Goal : Convert a CSV file into a file usabel with ELK Dev Tools  
Usage: python elk_bulk_convert_csv.py [option]
       CSV file must be:
        - First line = header with fields to add
        - First column = ELK index to update
        - Second column = action: create, update or delete
        - Third column = ELK doc id mandatory for update and delete

Options:
  -? | --help	    Show this help
  -v | --verbose    Print to output some messages for debuging
  -f | --infile     Input csv file name - Mandatory
  -o | --outfile    Output file for drag and drop in DEV ELK, if empty output is Console

Exemple:
python elk_bulk_convert_csv.py -f "C:\\temp\\file.csv" -v
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

###########################################################
# Global Variables
verbose = 0				# 1 for debugging mode
infilename = "test.csv"
outfilename = ""

###########################################################
# Def section - function

## Function which call the comment for usage at the beginning
def usage():
  print ( __doc__ )

def inputvar(argv):
  try:
  # To update with all possible arguments
    opts, args = getopt.getopt(argv, "?vf:o:", ["help","verbose","infile=","outfile="]) # see getopt python doc
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

  if (verbose):
    print ("------------------ START ------------------")
    print ("[DEBUG]file in \t= ", infilename)
    print ("[DEBUG]file out = ", outfilename)
    print ("-------------------------------------------")

##########################################################
## Function main
def main(argv):
  inputvar(argv)
  if ( outfilename != '' ):
    sys.stdout = open (outfilename,'w')
  line = 0
  with open(infilename, newline='') as f:
    reader = csv.reader(f, delimiter=';')
    print ('POST _bulk')
    for row in reader:
      if (line == 0 ):
      # First line of CSV file is the columns name
        frstl = row
      else:
      # We read each line colums by colums to create the bulk line
        i = 0
        tmpline = "{"
        actionline = ""
        for col in row:
          if ( i == 0 ):
          # ELK target index must be the first column
            elk_index = col
          elif ( i == 1 ):
           # ELK action must be the second column and must be create, delete or update
           elk_action = col
          elif ( i == 2 ):
            elk_id = col
            if ( elk_action == 'delete' or elk_action == 'update'):
            # For delete or update id or the ELK record is mandatory in colums 3
              actionline = '{"'+ elk_action +'":{"_index":"'+ elk_index +'","_id":"'+ elk_id +'"}}'
              if ( elk_id == "" ):
                print ("ERROR - Line ", line + 1, " of ", infilename, " ELK id is not empty")
                exit (1)
            else:
            # For create action even if id is given it will not be take into account
              actionline = '{"create":{"_index":"'+ elk_index +'"}}'            
          else:
          # For update or create we create the second line of data require by the ELK Bulk API
            tmpline = tmpline + "\"" + frstl[i] + "\":\"" + col + "\","
          i+=1
        print ( actionline )
        if ( elk_action == 'create' or elk_action == 'update'):
        # Only for create and update action we create the second line of bulk API
          size = len(tmpline)
          outline = tmpline[:size - 1]
          if ( elk_action == 'create'):
            print ( outline, '}' )
          else:
          # For update a special syntax is required at the begining
            print ( '{ "doc" : ', outline, '} }' )
      line+=1
        

##########################################################
## Program
if __name__ == "__main__":
  main(sys.argv[1:])
######################### END ############################
