# elk_toolbox
## python elk_bulk_convert_csv.py
**Goal**   
Convert a CSV file into a file usable with ELK Dev Tools or update ELK index directly     

**Prereq**   
CSV file must be:     
 -- First line = header with fields to add     
-- First column = ELK index to update     
-- Second column = action: create, update, delete or empty     
(if empty and -u is selected the line will become 'update')    
-- Third column = ELK doc id mandatory for update and delete    

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
