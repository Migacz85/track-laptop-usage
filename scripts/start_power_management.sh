#!/usr/bin/env bash
#
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

running_test="$( ps -efww | grep '[/]power_management.sh' )"
    if [[ ! -z $running_test ]]; then
        echo "[$(date)] : Process is already running $running_test"
        exit
    else
    bash $SCRIPTPATH/power_management.sh
    fi
