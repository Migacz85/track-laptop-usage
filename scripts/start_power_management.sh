#!/usr/bin/env bash
#
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

#enter to venv
source $SCRIPTPATH/charts/bin/activate

running_test="$( ps -efww | grep '[/]power_management.sh' )"
    if [[ ! -z $running_test ]]; then
        echo "[$(date)] : Power management already running $running_test"
    else

    (trap 'kill 0' SIGINT;
     bash $SCRIPTPATH/power_management.sh  &
     bash $SCRIPTPATH/track-laptop-usage.sh daily daily-laptop.log &
     bash $SCRIPTPATH/track-laptop-usage.sh hourly hourly-laptop.log
    )
    fi
