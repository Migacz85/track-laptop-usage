# Overview 

Scripts to give user information how long user was away after waking up
machine after suspend/hibernation mode. As well with tracking a total laptop
usage per day. And possibility to draw simple chart of user activity in `matplotlib` included.

# Features 

- Track your total laptop usage per day in houres [ track-laptop-usage.sh]
- Track how long user was away from your computer. [ power-management.sh ] 
- Control when your computer will be suspended. [ power-management.sh ]
  - Do not suspend if there is music playing on local sound card or bluetooth speaker
  - Do not suspend if camera will detect face
  - Suspend after X inactivity time
- Before going in to suspend mode check if user is sitting at front of computer: [ power-management.sh ]
  1. Make a picture
  2. Check if on picture is a face 
  3. If not - suspend. 

# Installation

On arch/manjaro run:
- `bash install.sh`

To start tracking total active usage time on computer run:
- `bash active.sh &`

To use face recognition before suspending computer and showing small
notification how long you was away from last time (and more):
- `bash active.sh start_power_management.sh`

# Settings 

You can set settings in `power_management.set` for example:
`bash
suspend_time_set=1              # Suspend computer after inactivity [minutes]
suspend_on_discharging_set="on" # set to "on" or "off"
suspend_on_charging_set="on"    #
`
After changing values restart of script is not needed

# Log files
By default you can find log files of active and away time in dir `log` in form:

- `| date_start | time_start | date_end   | time_end | time_away    |`
- `| 2020/02/04 | 12:28      | 2020/02/04 | 12:28    | 1396`        |`

`time_away` is measured in seconds. But in 'file time_suspend_h' there is human
readable form like `1h 34min`

In `active.csv` you can find total computer usage time by date in `seconds`
