#!/usr/bin/env bash
#
# Count total amount of seconds of laptop use. By each day.
#
########################################
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )" # Path of this script
MainPath=${SCRIPTPATH%/*}
track_type="$1"
FileName="$2"
########################################
track_till=120 #[sec] If user is idle for less than that, the active time on laptop will not count
DIR=$MainPath/log/ #DIR name need to end with / sign
sleep_time=60 #[sec] How often write to log file
########################################
FilePath="$DIR$FileName"

if [[ $1 != "daily" ]] && [[ $1 != "hourly" ]] && [[ $1 != "minutes" ]]; then
echo "No parameters provided"
echo "You need to specifiy type of tracking eg 'hourly' or 'daily' or 'minutes' and name of the faile example:"
echo "bash track-laptop-usgae.sh daily logfile.log"
exit
fi

function today {
  today=$( date +'%Y/%m/%d' )
  if [[ "$track_type" == "daily" ]]; then
  today=$( date +'%Y/%m/%d' )
  fi
  if [[ "$track_type" == "hourly" ]]; then
  today=$( date +'%Y/%m/%d %H' )
  fi
  if [[ "$track_type" == "minutes" ]]; then
  today=$( date +'%Y/%m/%d %H:%M' )
  fi
}
today

function show_time () {
    num=$1
    min=0
    hour=0
    day=0
    if((num>59));then
        ((sec=num%60))
        ((num=num/60))
        if((num>59));then
            ((min=num%60))
            ((num=num/60))
            if((num>23));then
                ((hour=num%24))
                ((day=num/24))
            else
                ((hour=num))
            fi
        else
            ((min=num))
        fi
    else
        ((sec=num))
    fi
    if [[ $day != 0 ]]; then
    echo "$day"d "$hour"h "$min"m
    elif [[ $hour != 0 ]]; then
    echo  "$hour"h "$min"m
    elif [[ $min != 0 ]]; then
    echo  "$min"m
    elif [[ $sec != 0 ]]; then
    echo  "$sec"s
    fi
}

function CreateFileIfNone {
    if [ ! -f $FilePath ]; then
      echo "data file not found, creating new one"
      mkdir -p $DIR
      cd $DIR
      echo  "date usage" > $FileName
      echo $today 0 >> $FileName
    fi
}

function GetLastSavedDate {
  line=$(tail -n 1 $FilePath )
  last_date=$(cut -d " " -f 1 <<< "$line")
}

function GetLastSavedValue {
  line=$(tail -n 1 $FilePath)
  last_saved_value=$(cut -d " " -f 2 <<< "$line")
}

function LazyUser {
      idle=$(xprintidle)
      idle=$(($idle / 1000))
      lazy_user=0

      if [[  $idle -gt $track_till ]]; then
      lazy_user=1
      fi

      if [[  $idle -eq $track_till ]]; then
      notify-send "$track_till seconds of inactivity" "This time dose not count to active time"
      fi

      echo "lazy user: $lazy_user Idle: $idle"
}

function UpdateTimeInFile {
      # today=$( date +'%Y/%m/%d' )
      today

        # Standardize timestamp format for comparison
        last_date_compare=$(echo "$last_date" | tr '|' ' ')
        today_compare=$(echo "$today" | tr '|' ' ')
        
        # Check if the last date in a file is same as today date
        if [[ "$last_date_compare" == "$today_compare" ]]; then
          # Count how long user spent on task
          time_diff=$last_saved_value+$sleep_time
          # Update time for today in file
          add_time=$(( $last_saved_value + $sleep_time ))
          # notify-send $(show_time $add_time)
          head -n -1 $FilePath > "$FileName.temp" ; mv "$FileName.temp" $FilePath
          echo "$today $add_time" >> $FilePath
        ## If not just add new date with counted time
        else
          echo "$today $sleep_time" >> $FilePath
        fi
}

########################################
while true;
    do

      sleep $sleep_time
      CreateFileIfNone
      LazyUser

      if [[  $lazy_user == 0 ]]; then
      GetLastSavedDate
      GetLastSavedValue
      UpdateTimeInFile
      fi


    done
