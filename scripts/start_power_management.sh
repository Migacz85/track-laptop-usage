#!/usr/bin/env bash
#
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

running_test="$( ps -efww | grep '[/]power_management.sh' )"
    if [[ ! -z $running_test ]]; then
        echo "[$(date)] : Power management already running $running_test"
    else
    bash $SCRIPTPATH/power_management.sh &
    fi

running_test="$( ps -efww | grep '[/]track-laptop-usage.sh' )"
    if [[ ! -z $running_test ]]; then
        echo "[$(date)] : Tracking laptop usage alreadyr running $running_test"
    else
    bash $SCRIPTPATH/track-laptop-usage.sh daily daily-laptop.csv &
    bash $SCRIPTPATH/track-laptop-usage.sh hourly hourly-laptop.log &
    fi
