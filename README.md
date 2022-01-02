# elk_toolbox
----------------
## python elk_bulk_convert_csv.py
**Goal** : Purpose of the program    
**Usage:** python elk_bulk_convert_csv.py [option]     
       CSV file must be:     
        - First line = header with fields to add     
        - First column = ELK index to update     
        - Second column = action: create, update or delete    
        - Third column = ELK doc id mandatory for update and delete    
**Options:**    
  -? | --help	    Show this help    
  -v | --verbose    Print to output some messages for debuging    
  -f | --infile     Input csv file name - Mandatory    
  -o | --outfile    Output file for drag and drop in DEV ELK, if empty output is Console     
Exemple:    
```python elk_bulk_convert_csv.py -f "C:\\temp\\file.csv" -v```    
