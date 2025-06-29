#!/usr/bin/env bash
set -e

TRACK_TYPE=${1:-daily}
LOG_FILE=${2:-daily-laptop.log}  # Default to daily log file
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
        hourly)  date +'%Y/%m/%d %H' ;;
        minutes) date +'%Y/%m/%d %H:%M' ;;
        *)       echo "Invalid track type: $TRACK_TYPE"; exit 1 ;;
    esac
}

# Get simplified timestamp for comparison
get_compare_timestamp() {
    case "$TRACK_TYPE" in
        daily)   date +'%Y/%m/%d' ;;
        hourly)  date +'%Y/%m/%d %H' ;;
        minutes) date +'%Y/%m/%d %H:%M' ;;
    esac
}

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Check if user is idle
is_idle() {
    if ! command -v xprintidle &> /dev/null; then
        echo "xprintidle not found! Please install it with: sudo apt-get install xprintidle"
        exit 1
    fi
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
    
    # Use a temporary file for atomic updates
    local temp_file="${LOG_PATH}.tmp"
    
    # Read the entire log file
    local lines=()
    while IFS= read -r line; do
        lines+=("$line")
    done < "$LOG_PATH"
    
    # Get the last line
    local last_line="${lines[-1]}"
    local last_date=${last_line%% *}
    local last_usage=${last_line##* }
    
    # For hourly tracking, compare just the date and hour portion
    if [[ "$TRACK_TYPE" == "hourly" ]]; then
        last_compare_date=$(echo "$last_date" | cut -d' ' -f1-2)
        current_compare_date=$(echo "$timestamp" | cut -d' ' -f1-2)
    else
        last_compare_date=$last_date
        current_compare_date=$timestamp
    fi
    
    # Update or add entry
    if [[ "$last_compare_date" == "$current_compare_date" ]]; then
        # Update the last line
        lines[-1]="$timestamp $((last_usage + SLEEP_TIME))"
    else
        # Add new entry
        lines+=("$timestamp $SLEEP_TIME")
    fi
    
    # Write to temporary file
    printf "%s\n" "${lines[@]}" > "$temp_file"
    
    # Atomically move the temporary file to the log file
    mv -f "$temp_file" "$LOG_PATH"
}

# Main loop
init_log
while true; do
    sleep "$SLEEP_TIME"
    if ! is_idle; then
        update_log
    fi
done
