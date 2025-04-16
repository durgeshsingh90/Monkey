#!/bin/sh
# --------------------------------------------------------------------------
# copyright, OmniPay 2011.  All rights reserved.
# --------------------------------------------------------------------------
#
# Update History
# --------------
# Date        By         Ver    Description
# 2017.Jul.19 KDuffy    1.0    Created
# This script extracts the rejectd entries from the trxn log files, if drops
# are found then the list is emailed to the Maillist
# Ensure that the specific variables are correct for the environment the script will be run on

################
# Set variables
################
# eMail distributtion list
#MAILLIST=ken.duffy@firstdata.com
MAILLIST=omnipay-authsupport@fiserv.com

# Sender email
#sender=oasis76@omnipay.ie
sender=oasis76@fiserv.com

scriptpath="/app/novate/scripts"
debugpath="/app/novate/logs/profiles/switch"
file_date_format="$(date '+%h%d_%Y').log"

sub_count=0

###################################################
# Extract reject entries from all trxn log files
###################################################

cat $debugpath/transaction.log | grep -e 'BCMC | 0.5        | "PU02"' -e 'BCMC | 0.5        | "S000"' -e 'BCMC | 0.5        | "I002"' -e 'BCMC | 0.5        | "IEER"' -e 'BCMC | 0.5        | "LENM"' -e 'BCMC
 | 0.5        | "NOTQ"' -e 'BCMC | 0.5        | "NOVS"' -e 'BCMC | 0.5        | "SOVF"' -e 'BCMC | 0.5        | "TOUT"' -e 'BCMC | 0.5        | "A001"' -e 'BCMC | 0.5        | "A002"' -e 'BCMC | 0.5
| "A003"' -e 'BCMC | 0.5        | "A004"' -e 'BCMC | 0.5        | "A006"' -e 'BCMC | 0.5        | "A013"' -e 'BCMC | 0.5        | "L000"' -e 'BCMC | 0.5        | "L003"' -e 'BCMC | 0.5        | "L010"' -e '
BCMC | 0.5        | "L011"' -e 'BCMC | 0.5        | "L012"' -e 'BCMC | 0.5        | "L013"' -e 'BCMC | 0.5        | "P' -e 'BCMC | 0.5        | "I' -e 'OMNIPAY | 39         | "09"'>  $scriptpath/BCMC_rejects.log

# Count the total number of reject entries
reject_count=$(grep -c "BCMC | 0.5        |" $scriptpath/BCMC_rejects.log)

if [ $reject_count -gt 0 ]; then

# Count and log each type of reject
{
    echo "Number of 'PU02' rejects: $(grep -c 'BCMC | 0.5        | "PU02"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'S000' rejects: $(grep -c 'BCMC | 0.5        | "S000"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'I002' rejects: $(grep -c 'BCMC | 0.5        | "I002"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'IEER' rejects: $(grep -c 'BCMC | 0.5        | "IEER"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'LENM' rejects: $(grep -c 'BCMC | 0.5        | "LENM"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'NOTQ' rejects: $(grep -c 'BCMC | 0.5        | "NOTQ"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'NOVS' rejects: $(grep -c 'BCMC | 0.5        | "NOVS"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'SOVF' rejects: $(grep -c 'BCMC | 0.5        | "SOVF"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'TOUT' rejects: $(grep -c 'BCMC | 0.5        | "TOUT"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'A001' rejects: $(grep -c 'BCMC | 0.5        | "A001"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'A002' rejects: $(grep -c 'BCMC | 0.5        | "A002"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'A003' rejects: $(grep -c 'BCMC | 0.5        | "A003"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'A004' rejects: $(grep -c 'BCMC | 0.5        | "A004"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'A006' rejects: $(grep -c 'BCMC | 0.5        | "A006"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'A013' rejects: $(grep -c 'BCMC | 0.5        | "A013"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'L000' rejects: $(grep -c 'BCMC | 0.5        | "L000"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'L003' rejects: $(grep -c 'BCMC | 0.5        | "L003"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'L010' rejects: $(grep -c 'BCMC | 0.5        | "L010"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'L011' rejects: $(grep -c 'BCMC | 0.5        | "L011"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'L012' rejects: $(grep -c 'BCMC | 0.5        | "L012"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'L013' rejects: $(grep -c 'BCMC | 0.5        | "L013"' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'Pccc' rejects: $(grep -c 'BCMC | 0.5        | "P' $scriptpath/BCMC_rejects.log)"
    echo "Number of 'Innn' rejects: $(grep -c 'BCMC | 0.5        | "I' $scriptpath/BCMC_rejects.log)"
} > $scriptpath/isobody.log

# Call the secondary script and capture its output
count_script_output=$($scriptpath/count_bcmc_rc_reject.sh)

# Append the output from the secondary script to the email body
echo "$count_script_output" >> $scriptpath/isobody.log

# Send email with attachment & body
(cat $scriptpath/isobody.log; uuencode $scriptpath/BCMC_rejects.log "BCMC_rejects_$file_date_format") | mailx -r $sender -s "$reject_count BCMC rejects on $(hostname)" $MAILLIST

fi
