# Toolbox to manage an ELK index with CSV or Excel files

## Technical architecture
This solution needs:    
- A GIT space to store the Excel or CSV files
- A Linux system able to access to the target ELK cluster and to GIT system
- An ELK cluster where the index will be store
- 2 scripts:
  * elk_bulk_convert.py to convert a CSV or Excel file into ELK API
  * auto_update_via_git.sh to run by CRON and pull new files from GIT    

## Setup the solution      
On the GIT create a project.
Configure the project in order to accept an SSH key to access to this project.
Store the files.   

For CSV file:        
    - File extension must be *.csv*
    - CSV is ";" separated    
For Excel extension must be *.xlsx*     


> Written with [StackEdit](https://stackedit.io/).

# elk_toolbox
## python elk_bulk_convert_csv.py
**Goal**   
Convert a CSV file into a file usable with ELK Dev Tools or update ELK index directly     

**Prereq**   
CSV file must be:     
- First line = header with fields to add     
- First column = ELK index to update     
- Second column = action: create, update, delete or empty     
(if empty and -u is selected the line will become 'update')    
- Third column = ELK doc id mandatory for update and delete    

**Options:**    
-? | --help	      : Show this help    
-v | --verbose    : Print to output some messages for debuging    
-f | --infile     : Input csv file name - Mandatory    
-o | --outfile    : Output file for drag and drop in DEV ELK, if empty output is Console    
-u | --update     : Update the ELK index in the cluster node (TLS must be activated in ELK)    
-c | --cacert     : ca.crt file for https ELK access [Mandatory if -u]    
-k | --key        : ELK API key with write role on target index [Mandatory if -u]   
-t | --url        : ELK url like https://localhost:9200 [Mandatory if -u]    

Exemple:    
```
python elk_bulk_convert_csv.py -f "C:\\temp\\file.csv" -v -o out.out -u -k tyyvhbkjvhcgchfc -t https://localhost:9200 -c ca.crt
```    
