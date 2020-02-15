#!/usr/bin/bash
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

source $SCRIPTPATH/charts/bin/activate
python $SCRIPTATH/chart.py &
deactivate
read

