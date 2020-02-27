#!/usr/bin/env bash
#
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
MainPath=${SCRIPTPATH%/*}

#enter to venv
source $MainPath/charts/bin/activate
running_test="$( ps -efww | grep '[/]power_management.sh' )"
    if [[ ! -z $running_test ]]; then
        echo "[$(date)] : Power management already running $running_test"
    else

    (trap 'kill 0' SIGINT;
     bash $SCRIPTPATH/power_management.sh
    )
    fi
