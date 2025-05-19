#!/bin/bash
#############################################################################################
# Script Name: autocmmtcmd.sh
#
# Description: This script automates cmmtcmd binary user interface (stop/start/status etc.) of all interface.
#
#            -  If the -a option is provided, all commands will run without asking for confirmation.
#            -  Otherwise, the script will ask for confirmation before executing each command containing the argument.
#
# Author: Durgesh Singh (F94GDOS)
# Date: 26 Febuary 2025
#
# Example:
#       1) autocmmtcmd.sh -a sta   --> Start all instances
#       2) autocmmtcmd.sh -a sto   --> Stop all instances
#       2) autocmmtcmd.sh sta      --> Prompts for execution of each Port
#
#
# Version History:
#    - Version 1.0 (2025-02-26) - Durgesh Singh - Initial version
#    - Version 2.0 (2025-05-19) - Durgesh Singh - Included cronjob changes.
##############################################################################################

# Function to display usage
usage() {
    echo "Usage: $0 [-a] <argument>"
    echo "  -a  Run all commands without asking for confirmation"
    echo "  <argument> Argument to be passed to the commands"
    echo "  autocmmtcmd.sh sta - to start one by one"
    echo "  autocmmtcmd.sh sto - to stop one by one"
    echo "  when -a is used, note that cronjob will be disabled before stopping the ports and enable after starting it"
    exit 1
}

# Check if the argument is provided
if [ $# -lt 1 ]; then
    usage
fi

# Parse the options
run_all=false
arg=""

while getopts "a" opt; do
    case ${opt} in
        a )
            run_all=true
            ;;
        \? )
            usage
            ;;
    esac
done
shift $((OPTIND -1))

# Get the remaining argument
if [ $# -ne 1 ]; then
    usage
else
    arg="$1"
fi

# Check and run the dormantCrontab script if necessary
if $run_all && [ "$arg" = "sto" ]; then
    /usr/local/scripts/oasis76/dormantCrontab.sh
    sleep 2
    echo "Crontab status: Dormant"
fi

# Define commands in an array
commands=(
    "cmmtcmd -i CMMTAPACS -c $arg       #APACS"
    "cmmtcmd -i CMMTAPACS -c s          #APACS"
    "cmmtcmd -i CMMTISO7532 -c $arg     #Telecash"
    "cmmtcmd -i CMMTISO7532 -c s        #Telecash"
    "cmmtcmd -i CMMTISO -c $arg         #VPNs"
    "cmmtcmd -i CMMTISO -c s            #VPNs"
    "cmmtcmd -i CMMTISO7536 -c $arg     #PayPal-1"
    "cmmtcmd -i CMMTISO7536 -c s        #PayPal-1"
    "cmmtcmd -i CMMTISO7563 -c $arg     #PayPal-2"
    "cmmtcmd -i CMMTISO7563 -c s        #PayPal-2"
    "cmmtcmd -i CMMTISO7564 -c $arg     #PayPal-3"
    "cmmtcmd -i CMMTISO7564 -c s        #PayPal-3"
    "cmmtcmd -i CMMTISO37536 -c $arg    #PayPal-1 (Fixed Line)"
    "cmmtcmd -i CMMTISO37536 -c s       #PayPal-1 (Fixed Line)"
    "cmmtcmd -i CMMTISO37563 -c $arg    #PayPal-2 (Fixed Line)"
    "cmmtcmd -i CMMTISO37563 -c s       #PayPal-2 (Fixed Line)"
    "cmmtcmd -i CMMTISO37564 -c $arg    #PayPal-3 (Fixed Line)"
    "cmmtcmd -i CMMTISO37564 -c s       #PayPal-3 (Fixed Line)"
    "cmmtcmd -i CMMTISO7537 -c $arg     #SUMUP"
    "cmmtcmd -i CMMTISO7537 -c s        #SUMUP"
    "cmmtcmd -i CMMTISO7538 -c $arg     #Payvision JCB"
    "cmmtcmd -i CMMTISO7538 -c s        #Payvision JCB"
    "cmmtcmd -i CMMTISO7540 -c $arg     #Unused"
    "cmmtcmd -i CMMTISO7540 -c s        #Unused"
    "cmmtcmd -i CMMTISO7542 -c $arg     #Clearhaus"
    "cmmtcmd -i CMMTISO7542 -c s        #Clearhaus"
    "cmmtcmd -i CMMTISO7570 -c $arg     #BrainTree-1"
    "cmmtcmd -i CMMTISO7570 -c s        #BrainTree-1"
    "cmmtcmd -i CMMTISO7571 -c $arg     #BrainTree-2"
    "cmmtcmd -i CMMTISO7571 -c s        #BrainTree-2"
    "cmmtcmd -i CMMTISO7572 -c $arg     #BrainTree-3"
    "cmmtcmd -i CMMTISO7572 -c s        #BrainTree-3"
    "cmmtcmd -i CMMTISO37570 -c $arg    #BrainTree-4"
    "cmmtcmd -i CMMTISO37570 -c s       #BrainTree-4"
    "cmmtcmd -i CMMTISO37571 -c $arg    #BrainTree-5"
    "cmmtcmd -i CMMTISO37571 -c s       #BrainTree-5"
    "cmmtcmd -i CMMTISO37572 -c $arg    #BrainTree-6"
    "cmmtcmd -i CMMTISO37572 -c s       #BrainTree-6"
)

# Iterate over the commands array and execute each command
for cmd in "${commands[@]}"; do
    echo "================================================="
    if $run_all || [[ "$cmd" != *"$arg"* ]]; then
        echo "Executing: $cmd"
        eval $cmd
    else
        read -p "Execute '$cmd'? (y/n): " choice
        if [ "$choice" = "y" ]; then
            echo "Executing: $cmd"
            echo ""
            eval $cmd
        else
            echo "Skipping: $cmd"
        fi
    fi
done

# Check and run the activeCrontab script if necessary
if $run_all && [ "$arg" = "sta" ]; then
    sleep 5
    /usr/local/scripts/oasis76/activeCrontab.sh
    echo "Crontab status: Active"

fi

echo "All commands executed."

