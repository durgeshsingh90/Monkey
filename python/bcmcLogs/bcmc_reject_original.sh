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
file_date_format="`date '+%h%d_%Y'`.log"

#S000_count=0
#PU02_count=0
sub_count=0

###################################################
# Extract reject entries from all trxn log files
###################################################


#cat $debugpath/transaction.log | grep -e  '"BCMC | 0.5        | "A004"'>  $scriptpath/BCMC_rejects.log
#cat $debugpath/transaction.log | grep -e "PU02" -e "I002" -e "IERR" -e "LENM"  -e "NOTQ" -e "NOVS" -e "SOVF" -e "TOUT" -e "BCMC | 0.5        | "P -e "BCMC | 0.5        | "I -e "UKSV" -e "A001" -e "A002" -e
 "A003" -e "A005" -e "A006" -e "A013" -e "L000" -e "L003" -e "L010" -e "L011" -e "L012" -e "L013" -e "L021" -e "L022" -e "L023" -e "S000" -e "BCMC | 0.5        | "A>  $scriptpath/BCMC_rejects.log
cat $debugpath/transaction.log | grep -e 'BCMC | 0.5        | "PU02"' -e 'BCMC | 0.5        | "S000"' -e 'BCMC | 0.5        | "I002"' -e 'BCMC | 0.5        | "IEER"' -e 'BCMC | 0.5        | "LENM"' -e 'BCMC
 | 0.5        | "NOTQ"' -e 'BCMC | 0.5        | "NOVS"' -e 'BCMC | 0.5        | "SOVF"' -e 'BCMC | 0.5        | "TOUT"' -e 'BCMC | 0.5        | "A001"' -e 'BCMC | 0.5        | "A002"' -e 'BCMC | 0.5
| "A003"' -e 'BCMC | 0.5        | "A004"' -e 'BCMC | 0.5        | "A006"' -e 'BCMC | 0.5        | "A013"' -e 'BCMC | 0.5        | "L000"' -e 'BCMC | 0.5        | "L003"' -e 'BCMC | 0.5        | "L010"' -e '
BCMC | 0.5        | "L011"' -e 'BCMC | 0.5        | "L012"' -e 'BCMC | 0.5        | "L013"' -e 'BCMC | 0.5        | "P' -e 'BCMC | 0.5        | "I' -e 'OMNIPAY | 39         | "09"'>  $scriptpath/BCMC_rejects.log

#########################################################
# If drops are found in the ISO file then send out email
#########################################################
#reject_count=`cat $scriptpath/BCMC_rejects.log | grep -v "PU02"
#reject_count=`cat $scriptpath/BCMC_rejects.log | grep -c "REJECT_CODE"`
reject_count=`cat $scriptpath/BCMC_rejects.log | grep -c "BCMC | 0.5        |"`

if [[ $reject_count > 0 ]]
    then

#Count PU02 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "PU02"' $scriptpath/BCMC_rejects.log)
echo "Number of 'PU02' rejects: $sub_count\n" >  $scriptpath/isobody.log

#Count S000 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "S000"' $scriptpath/BCMC_rejects.log)
echo "Number of 'S000' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#Count I002 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "I002"' $scriptpath/BCMC_rejects.log)
echo "Number of 'I002' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#Count IEER rejects
sub_count=$(grep -c 'BCMC | 0.5        | "IEER"' $scriptpath/BCMC_rejects.log)
echo "Number of 'IEER' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#Count LENM rejects
sub_count=$(grep -c 'BCMC | 0.5        | "LENM"' $scriptpath/BCMC_rejects.log)
echo "Number of 'LENM' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#Count NOTQ rejects
sub_count=$(grep -c 'BCMC | 0.5        | "NOTQ"' $scriptpath/BCMC_rejects.log)
echo "Number of 'NOTQ' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#Count NOVS rejects
sub_count=$(grep -c 'BCMC | 0.5        | "NOVS"' $scriptpath/BCMC_rejects.log)
echo "Number of 'NOVS' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#Count SOVF rejects
sub_count=$(grep -c 'BCMC | 0.5        | "SOVF"' $scriptpath/BCMC_rejects.log)
echo "Number of 'SOVF' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count TOUT rejects
sub_count=$(grep -c 'BCMC | 0.5        | "TOUT"' $scriptpath/BCMC_rejects.log)
echo "Number of 'TOUT' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count A001 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "A001"' $scriptpath/BCMC_rejects.log)
echo "Number of 'A001' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count A002 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "A002"' $scriptpath/BCMC_rejects.log)
echo "Number of 'A002' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count A003 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "A003"' $scriptpath/BCMC_rejects.log)
echo "Number of 'A003' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count A004 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "A004"' $scriptpath/BCMC_rejects.log)
echo "Number of 'A004' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count A005 rejects
#sub_count=$(grep -c 'BCMC | 0.5        | "A005"' $scriptpath/BCMC_rejects.log)
#echo "Number of 'A005' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count A006 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "A006"' $scriptpath/BCMC_rejects.log)
echo "Number of 'A006' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count A013 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "A013"' $scriptpath/BCMC_rejects.log)
echo "Number of 'A013' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count L000 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "L000"' $scriptpath/BCMC_rejects.log)
echo "Number of 'L000' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count L003 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "L003"' $scriptpath/BCMC_rejects.log)
echo "Number of 'L003' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count L010 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "L010"' $scriptpath/BCMC_rejects.log)
echo "Number of 'L010' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count L011 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "L011"' $scriptpath/BCMC_rejects.log)
echo "Number of 'L011' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count L012 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "L012"' $scriptpath/BCMC_rejects.log)
echo "Number of 'L012' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count L013 rejects
sub_count=$(grep -c 'BCMC | 0.5        | "L013"' $scriptpath/BCMC_rejects.log)
echo "Number of 'L013' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count Pccc rejects
sub_count=$(grep -c 'BCMC | 0.5        | "P' $scriptpath/BCMC_rejects.log)
echo "Number of 'Pccc' rejects: $sub_count\n" >>  $scriptpath/isobody.log

#count Innn rejects
sub_count=$(grep -c 'BCMC | 0.5        | "I' $scriptpath/BCMC_rejects.log)
echo "Number of 'Innn' rejects: $sub_count\n" >>  $scriptpath/isobody.log


#echo "Number of 'PU02' rejects: $PU02_count" >  $scriptpath/isobody.log
#echo "" >> $scriptpath/isobody.log
#echo "Other dropped types: $(($drop_count-$Conxn_count-$CFA_count-$BM39_count-$BM49_count-$BM60_count-$BM61_count-$BM90_count))" >> $scriptpath/isobody.log
#echo " " >> $scriptpath/isobody.log

# Call the secondary script and capture its output
count_script_output=$($scriptpath/count_bcmc_rc_reject.sh)

# Append the output from the secondary script to the email body
echo "$count_script_output" >> $scriptpath/isobody.log

# Send email with attachment & body
(cat $scriptpath/isobody.log; uuencode $scriptpath/BCMC_rejects.log "BCMC_rejects_$file_date_format") | mailx -r $sender -s "$reject_count BCMC rejects on $(hostname)" $MAILLIST

fi
