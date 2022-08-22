# Toolbox to manage an ELK index with CSV or Excel files

## Setup the solution      
### 1 - GITLAB    
On the GITLAB, create a project where you will store the CSV or Excel files.    
On the GITLAB create an access token for this project that we are going to use for push/pull:     
    - Menu => Settings => Access Tokens    
    - Give a token name which will be used as username with [token_name]_bot, ie: automat     
    - Select write_repository authorization      
    - Generate the token and secure it because it will be used later as password       

### 2 - Linux server (RedHat / CentOS)    
Check the following prerequisites:    
   - GIT package must be installed: rpm -qa | grep git       
   - Python 3 must be installed: python -V or python3-V     
   - Package curl must be installed: curl -h
   - Following python module must be installed:     
          - requests
          - datetime
          - pandas
 
On the linux gateway server create a dedicated user:
```
useradd -c "Automation user" -d /home/automat -m automat
```
Create a directory for the script: 
```
mkdir soft
```
Store the 2 scripts:       
  * elk_bulk_convert.py to convert a CSV or Excel file into ELK API       
  * auto_update_via_git.sh to run by CRON and pull new files from GIT     

Create a directory that will be synchronized with the GIT:     
```
mkdir elk_git_file
```
Go to this directory and clone the GIT project inside:
```
cd ~/elk_git_file
git clone https://git.atosone.com/my_project/threshold_index.git
Cloning into 'threshold_index'...
Username for 'https://git.com': automat_bot
Password for 'https://automat_bot@git.com': [automat_token]
remote: Enumerating objects: 363, done.
remote: Counting objects: 100% (97/97), done.
remote: Compressing objects: 100% (54/54), done.
remote: Total 363 (delta 56), reused 76 (delta 43), pack-reused 266
Receiving objects: 100% (363/363), 167.56 KiB | 2.94 MiB/s, done.
Resolving deltas: 100% (191/191), done.
```
REM: *in order to store the token locally execute the following git command:*
```
cd ~/elk_git_file/threshold_index
git config credential.helper store
```
*Next time the username/password will be requested, they will be stored permanently encrypted in the .git local directory.*     

### 3 - ELK / Kibana interface    
Done with ELK version 7.16 or above.    
We need to  create a index called "threshold".    
We start by creating an API-KEY to allow read/write on this index.    
On Kibana:
- Menu => Management => Stack Management    
- Security => API keys     
- Give a name: automat_key    
- Select "Restrict privileges", in the section indices, names replace * by threshold*.    
- Create API key and store the result in a secure location.    

### 4 - Linux server / finalization 
On the Linux go to soft directory.
Open script auto_update_via_git.sh and update the variables at the beginning:
    - DIR_INDEX= location of the CSV and Excel file to check , ie: /home/automat/elk_git_file/threshold_index    
    - APIKEY= ELK API key previously created     
    - ELKSRV= IP or FQDN of the ELK node to use ie, hot node     
    - CACRT= location of the ca.crt certificat to connect to ELK    
 Create a test .csv file:
 ```
cat << EOF > test.csv
_index;action;_id;type;scope;crit_priority;crit_value;warn_priority;warn_value;instance;category
threshold;create;;my_type;my_scope;high;0.9;medium;0.8;my_instance;my_category
EOF
```
 Test this file to see if access to ELK is ok:
```
python /home/automat/soft/elk_bulk_convert.py -c ca.crt -k NzdzWERuOEI1YTU4eU5UOGRTNEM6MVRNeGxzejFTVUM3M3R0b29zUkNiQQ== -t "https://localhost:9200" -f test.csv -v -u    
```
The feedback of the script in verbose (-v ) mode is:
```
------------------ START :  19/02/2022 14:43:30  ----------------------------
[DEBUG]file in  =  test.csv
[DEBUG]file out =
[DEBUG]directory =
[DEBUG]update =  1
[DEBUG]url =  https://localhost:9200
[DEBUG]key =  NzdzWERuOEI1YTU4eU5UOGRTNEM6MVRNeGxzejFTVUM3M3R0b29zUkNiQQ==
[DEBUG]ca.crt file =  ca.crt
-----------------------------------------------------------------------------
[DEBUG]Number of lines   =  2
[DEBUG]Number of columns =  12
-----------------------------------------------------------------------------
[DEBUG] Update requested (create/update/delete):  1
-----------------------------------------------------------------------------
[DEBUG]  curl -k --cacert ca.crt -H "Authorization: ApiKey NzdzWERuOEI1YTU4eU5UOGRTNEM6MVRNeGxzejFTVUM3M3R0b29zUkNiQQ==" -H "Content-Type: application/json" -X POST "https://localhost:9200/_bulk?pretty" --data-binary "@test.csv.tmp" > curl.out
-----------------------------------------------------------------------------
[DEBUG] Update initial file test.csv  after ELK bulk update
[DEBUG] files curl.out and  test.csv.tmp  not deleted
------------------- END:  19/02/2022 14:43:30   -----------------------------
```
In case of issue, try to execute the curl command given to see the result.    

When everything is good, you can schedule every 5 minutes on the crontab the script  *auto_update_via_git.sh*.    

## Threshold update use

Mechanism is based on GIT and the server linux server able to do API Bulk to ELK Stack.      

Inside the csv file only the 3rd fist colomns are mandatory:      

- Fist column is "-index": the ELK index to update, for Sephora it's always "threshold"     
- Second column is "action" the action to perform :
	- If **empty** nothing is done,
	- If **create**, the line is added and column 3 can be empty,
	- If **update**, the line will update the record number given in column 3 (mandatory),
 	- If **delete**, the record number given in column 3 (mandatory) will be deleted from the index
- Third column is "_id", the number inside is the index record uniq number mandatory for update and delete.

After ELK index update, the file used is renamed with extension .bkp. This file can be used to restore data if needed.   
A file with the same name is created and all action are columns are emptied except for line which were deleted, they are no longer in the file.    
New files ".csv" and ".bkp" are git pushed back to the GIT repository and the comment of commit is the date of execution.    
In case of issue during update, action column state could be replaced by ERROR. This means that an error occured when update was done.     
In that case you find on linux server a file .tmp extension with not null size.    
This file contain the line normally used by the ELK API Bulk to update index.     
To test it to see why update failed, copy the content of the file to ELK Dev Tool Console and add before the line: `POST _bulk` and the content, or the line to test.

     
> Written with [StackEdit](https://stackedit.io/).
