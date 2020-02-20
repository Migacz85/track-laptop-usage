# Overview 

Be mindfull how much daily and in what houres you are using your computer. 
Track your total laptop usage per day. Be informed how long you was away from
computer after waking up your machine in small handy notification. 
Check detailed information when and how long you was active or away from
computer in nicley plotted heatmap chart.
As a bonus suspend your computer in more intelligent way. 

# Features 

## Tracking features
- Track your total laptop usage per day in houres, and total daily usage [ track-laptop-usage.sh]
- Give short information to user as soon as lid is open: 
  - how long computer was suspended [ power-management.sh]
  - how long computer was hibernated. [ power-management.sh] 
- Make a simple chart showing how long computer was used on daily basis. [ track-laptop-usage.sh, show-graph.sh, chart.py ]

## Charting
- Plot bar chart of total usage time per day.
- Plot heatmap of laptop usage in hourly precision.
  -A day is divided in 24 hours, if user spent whole time in this hour without
  any breaks this hour is counted as 60 (60 whole minutes that user spent in
  this hour). If for example user had 15 minutes break in given hour it will
  result in score 45.

![Heatmap](https://i.imgur.com/FTpKIK1.png)

## Power management features
- Control when user computer will be suspended. [ power-management.sh ]
  - Suspend after X inactivity time
  - Do not suspend if there is music playing on local sound card or Bluetooth speaker
- Before going in to suspend mode check if user is sitting at front of computer: [ power-management.sh ]
  1. Make a picture
  2. Check if on picture is a face 
  3. If not - suspend. 
  4. Last check is stored in `suspend_check.jpg` file
- Prevent from running script twice [ start_power_management.sh ]


# Bugs:

- [x] Once I found computer was not supsending because sound card was giving
      false information that is "RUNNING", `pulseaudio -k`, imediattely solved problem.

# Installation

On arch/manjaro run:
- `bash install.sh`
if you are on different distro inspect `install.sh` and install packages
specified in this file using your package mangager.

To start tracking time - and suspending computer shortly after when you are away.
- `bash start_power_management.sh`

Or if you want just to track time without controlling when your laptop will be
suspended, start this script on every fresh start of your system: 

- ` bash track-laptop-usage.sh daily daily-laptop.log `
- ` bash track-laptop-usage.sh hourly hourly-laptop.log `

Note: 
Beware that way you will track how long your computer was turn on.
So if you will go away, and your computer will be open this will count.
You can set your current power management to suspend your computer more quickly.

To show plot you need to run:
- `bash show-graph.sh` 

# Settings 

You can set settings in `power_management.set` for example:
`bash
suspend_time_set=1              # Suspend computer after inactivity [minutes]
suspend_on_discharging_set="on" # set to "on" or "off"
suspend_on_charging_set="on"    #
`
After changing values restart of script is not needed

# Troubleshooting
    
If you encounter problems you can run directly: 

- `bash power_management.sh`

1. Check if .log files are created in log folder and records created.
2. Check if path to log file in `chart.py` is correct 

# TODO: 
- [ ] Do not suspend computer if there is ongoing installation from pacman.
- [ ] Notify user that he exceeded productive daily/weekly limit of hours.
- [ ] Simplify installation process to bare minimum.

# Summary 

Overall this is small nice tool to play with :) 
