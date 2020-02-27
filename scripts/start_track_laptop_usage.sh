#!/usr/bin/env bash
#
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
MainPath=${SCRIPTPATH%/*}

#enter to venv
source $MainPath/charts/bin/activate
running_test="$( ps -efww | grep '[/]track-laptop-usage.sh' )"
    if [[ ! -z $running_test ]]; then
        echo "[$(date)] : Power management already running $running_test"
    else

    (trap 'kill 0' SIGINT;
     bash $SCRIPTPATH/track-laptop-usage.sh daily daily-laptop.log &
     bash $SCRIPTPATH/track-laptop-usage.sh hourly hourly-laptop.log
    )
    fi
