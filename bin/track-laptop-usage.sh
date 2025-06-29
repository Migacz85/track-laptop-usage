#!/usr/bin/env bash
set -e

TRACK_TYPE=${1:-daily}
LOG_FILE=${2:-$TRACK_TYPE-laptop.log}
TRACK_TILL=120  # seconds of idle time
SLEEP_TIME=60   # seconds between checks
LOG_DIR="$(dirname "$0")/../log"
LOG_PATH="$LOG_DIR/$LOG_FILE"

# Create log directory if needed
mkdir -p "$LOG_DIR"

# Get current timestamp based on track type
get_timestamp() {
    case "$TRACK_TYPE" in
        daily)   date +'%Y/%m/%d' ;;
        hourly)  date +'%Y/%m/%d|%H' ;;
        minutes) date +'%Y/%m/%d|%H:%M' ;;
        *)       echo "Invalid track type: $TRACK_TYPE"; exit 1 ;;
    esac
}

# Check if user is idle
is_idle() {
    idle_ms=$(xprintidle)
    idle_sec=$((idle_ms / 1000))
    [[ $idle_sec -gt $TRACK_TILL ]]
}

# Initialize log file if needed
init_log() {
    if [[ ! -f "$LOG_PATH" ]]; then
        echo "date usage" > "$LOG_PATH"
        echo "$(get_timestamp) 0" >> "$LOG_PATH"
    fi
}

# Update log with current usage
update_log() {
    local timestamp=$(get_timestamp)
    local last_line=$(tail -n 1 "$LOG_PATH")
    local last_date=${last_line%% *}
    local last_usage=${last_line##* }

    if [[ "$last_date" == "$timestamp" ]]; then
        # Update existing entry
        head -n -1 "$LOG_PATH" > "$LOG_PATH.tmp"
        mv "$LOG_PATH.tmp" "$LOG_PATH"
        echo "$timestamp $((last_usage + SLEEP_TIME))" >> "$LOG_PATH"
    else
        # Add new entry
        echo "$timestamp $SLEEP_TIME" >> "$LOG_PATH"
    fi
}

# Main loop
init_log
while true; do
    sleep "$SLEEP_TIME"
    if ! is_idle; then
        update_log
    fi
done
