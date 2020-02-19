#!/usr/bin/env bash
#
# Count total amount of seconds of laptop use. By each day.
#
########################################
DIR=~/stats/log/ #DIR name need to end with / sign
FileName="$2"
FilePath="$DIR$FileName"
sleep_time=60 #How often log active time
track_type="$1"
########################################

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
  today=$( date +'%Y/%m/%d|%H' )
  fi
  if [[ "$track_type" == "minutes" ]]; then
  today=$( date +'%Y/%m/%d|%H:%M' )
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

function UpdateTimeInFile {
      sleep $sleep_time
      # today=$( date +'%Y/%m/%d' )
      today
        ## Check if the last date in a file is same as today date
        if [[ $last_date == $today ]]; then
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
      CreateFileIfNone
      GetLastSavedDate
      GetLastSavedValue
      UpdateTimeInFile
    done
