#!/usr/bin/env bash
set -euo pipefail

# Configuration
TRACK_TYPE=${1:-daily}
LOG_FILE=${2:-daily-laptop.log}
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
        *)       echo "Invalid track type: $TRACK_TYPE" >&2; exit 1 ;;
    esac
}

# Check if user is idle
is_idle() {
    if ! command -v xprintidle &> /dev/null; then
        echo "xprintidle not found! Please install it with: sudo apt-get install xprintidle" >&2
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
    local temp_file="${LOG_PATH}.tmp"
    
    # Read and process the log file
    local last_line=""
    local last_date=""
    local last_usage=0
    local updated=false
    
    # Process the log file line by line
    while IFS= read -r line; do
        # Skip header line
        if [[ "$line" == "date usage" ]]; then
            echo "$line" > "$temp_file"
            continue
        fi
        
        # Parse the line
        current_date=${line%% *}
        current_usage=${line##* }
        
        # Check if this is the current hour/day
        if [[ "$current_date" == "$timestamp" ]]; then
            # Update the usage for this period
            last_line="$timestamp $((current_usage + SLEEP_TIME))"
            last_date="$current_date"
            last_usage=$((current_usage + SLEEP_TIME))
            updated=true
        else
            # Write previous lines as-is
            echo "$line" >> "$temp_file"
        fi
    done < "$LOG_PATH"
    
    # If we didn't find an entry for this period, add a new one
    if ! $updated; then
        last_line="$timestamp $SLEEP_TIME"
    fi
    
    # Add the last (updated or new) entry
    echo "$last_line" >> "$temp_file"
    
    # Atomically replace the log file
    mv -f "$temp_file" "$LOG_PATH"
}

# Main execution
init_log
while true; do
    sleep "$SLEEP_TIME"
    if ! is_idle; then
        update_log
    fi
done
