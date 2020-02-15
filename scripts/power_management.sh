#!/usr/bin/env bash
#Global variable
hibernation=0

if [ ! -f $file_path ] || [ ! -f $file_path_h ]; then
    echo "data file not found, creating new one"
    mkdir -p $log_dir
    cd $log_dir
    echo "date_start time_start date_end time_end time_suspend "  > $log_name
    echo "date_start time_start date_end time_end time_suspend "  > $log_name_h
fi

# Information to the user
function information_to_user {
        clear
        echo "I will hibernate when battery will be bellow $hibernation_percentage_set%"
        echo "I will suspend computer after $(($suspend_time_set/60000)) minutes"
        echo "Stats how long user was away will be saved in: "
        echo
        echo  $file_path
        echo  $file_path_h
}

# Functions

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

function monitor_battery_and_hibernate() {
    if [[ $hibernation -eq 1 ]]; then
        sleep 10
        echo "Resurrection... "

        sleep_time=$(show_time $SECONDS)
        echo $sleep_time
        notify-send "I was hibernated for: $sleep_time "
         # Saving to log
         notify-send "Welcome back" "You was away for: $away_time"
         echo -n $(date +'%Y/%m/%d %H:%M' --date="-$away_time_sec sec")" "$(date +'%Y/%m/%d %H:%M') >> $file_path
         echo " "$(($SECONDS)) >> $file_path
         #Human read
         echo -n $(date +'%Y/%m/%d %H:%M' --date="-$away_time_sec sec")" "$(date +'%Y/%m/%d %H:%M') >> $file_path_h
         echo " "$sleep_time >> $file_path_h

        echo "Script will start monitoring battery after $delay_after_waking_up seconds."
        sleep $delay_after_waking_up
    else
        sleep 0
    fi
    hibernation=0

    battery="$( upower -i $(upower -e | grep '/battery') | grep --color=never -E percentage|xargs|cut -d' ' -f2|sed s/%// )"
    charging_state="$( upower -i $(upower -e | grep '/battery') | grep --color=never -E charging|xargs|cut -d' ' -f2|sed s/%// )"

    if [[ $battery -lt $hibernation_percentage_set ]] && [[ $charging_state == "discharging" ]]; then
        SECONDS=0
        echo "Battery level is: $battery"
        echo "Running hibernation command..."
        systemctl hibernate
        hibernation=1
    fi
    }

function monitor_suspend_time() {

  #Test if clock is not disrupted by system suspend
  #Test how many packages are sent to bluetooth in one second
  time1=$( date +'%s' )
  bluetooth_rx=$(hciconfig | grep "RX bytes" | awk -F':' '{print $2}' | awk -F' ' '{print $1}')
  sleep 1
  time2=$(($( date +'%s') - 1 ))
  bluetooth_rx2=$(hciconfig | grep "RX bytes" | awk -F':' '{print $2}' | awk -F' ' '{print $1}')


  idle=$(xprintidle)

  if [[ $bluetooth_rx!="" ]] && [[ $bluetooth_rx2!="" ]]; then
    bluetooth_music=$((bluetooth_rx-bluetooth_rx2))
  fi


   music_playing="$(cat /proc/asound/card*/pcm*/sub*/status | grep "RUNNING")" # state: RUNNING
   if [[ $music_playing == "state: RUNNING" ]] || [[  $bluetooth_music > 100 ]]; then
      music_playing=1
      else
      music_playing=0
   fi

   battery="$( upower -i $(upower -e | grep '/battery') | grep --color=never -E percentage|xargs|cut -d' ' -f2|sed s/%// )"
    #When battery is 100% is not showing "discharging" but some wierd stuff
   charging_state="$( upower -i $(upower -e | grep '/battery') | grep --color=never -E state|xargs|cut -d' ' -f2|sed s/%// )"

    if [[ $charging_state = "fully-charged" ]] ; then
        charging_state="charging"
    fi

    echo -en "\r Rx:$bluetooth_rx Tx:$bluetooth_rx2 Battery: $battery Charging_state:$charging_state Music_playing: $music_playing Suspend_after[m]: $(($suspend_time_set/60/1000)) Idle: $(($idle/1000))"

    if [[ $idle -gt $suspend_time_set ]] && [[ $music_playing == 0 ]]; then

        ffmpeg -f video4linux2 -s 1920x1080 -i /dev/video0 -ss 0:0:2 -frames 1 ~/stats/suspend_check.jpg -y &
        face=$(face_detection ~/stats/suspend_check.jpg)
        if [[ $face != "" ]]; then
            xdotool mousemove 1000 500 # idle=0
        fi


        if   [[ $battery == "100" ]] && [[ $suspend_on_discharging_set == "on" ]] && [[ $face == "" ]] ; then
            systemctl suspend
            xdotool mousemove 1000 500 # idle=0
        fi

        if   [[ $charging_state == "discharging" ]] && [[ $suspend_on_discharging_set == "on" ]] && [[ $face == "" ]] ; then
            systemctl suspend
            xdotool mousemove 1000 500 # idle=0
        fi

        if   [[ $charging_state == "charging" ]] && [[ $suspend_on_charging_set == "on" ]] && [[ $face == "" ]] ; then
            systemctl suspend
            xdotool mousemove 1000 500 # idle=0
        fi

    fi

  if [[ $time1 != $time2 ]]; then
     away_time_sec=$(( $time2 - $time1))
     # Save only when user was away more than X seconds
     if (( $away_time_sec > $min_time_to_log )); then
         away_time_h=$(show_time $(($time2-$time1)))

         # Saving to log
         notify-send "Welcome back" "You was away for: $away_time_h"
         echo -n $(date +'%Y/%m/%d %H:%M' --date="-$away_time_sec sec")" "$(date +'%Y/%m/%d %H:%M') >> $file_path
         echo " "$away_time_sec >> $file_path
         #Human read
         echo -n $(date +'%Y/%m/%d %H:%M' --date="-$away_time_sec sec")" "$(date +'%Y/%m/%d %H:%M') >> $file_path_h
         echo " "$away_time_h >> $file_path_h
         #Active time 
         # echo -n $(date +'%Y/%m/%d %H:%M') >> $DIR3
         # echo " "$detect_suspend_mode >> $DIR3

     fi
  fi
 }

# Main loop
for (( i = 0; i == 0; )); do
    source $HOME/stats/scripts/power_management.set
    suspend_time_set=$(($suspend_time_set * 60000))
    # information_to_user
    monitor_suspend_time
    monitor_battery_and_hibernate
done
