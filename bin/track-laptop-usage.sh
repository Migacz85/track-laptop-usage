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
        hourly)  date +'%Y/%m/%d %H' ;;  # Use space as delimiter
        minutes) date +'%Y/%m/%d %H:%M' ;;
        *)       echo "Invalid track type: $TRACK_TYPE" >&2; exit 1 ;;
    esac
}

# Check if user is idle using multiple methods
is_idle() {
    # Method 1: Check X11 idle time
    if command -v xprintidle &> /dev/null; then
        idle_ms=$(xprintidle)
        idle_sec=$((idle_ms / 1000))
        if (( idle_sec > TRACK_TILL )); then
            return 0
        fi
    fi

    # Method 2: Check console idle time
    if who -u &> /dev/null; then
        console_idle=$(who -u | awk '{print $6}' | cut -d: -f2)
        if (( console_idle > TRACK_TILL )); then
            return 0
        fi
    fi

    # Method 3: Fallback to /proc/uptime
    if [[ -f /proc/uptime ]]; then
        read -r uptime idle_time < /proc/uptime
        if (( $(echo "$idle_time > $TRACK_TILL" | bc -l) )); then
            return 0
        fi
    fi

    # If none of the methods detected idle, assume active
    return 1
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
    
    # Read the entire log file into memory
    mapfile -t lines < "$LOG_PATH"
    
    # Process each line
    local updated=false
    for i in "${!lines[@]}"; do
        line="${lines[$i]}"
        
        # Skip header line
        if [[ "$line" == "date usage" ]]; then
            continue
        fi
        
        # Parse the line
        current_date=${line%% *}
        current_usage=${line##* }
        
        # Check if this is the current hour
        if [[ "$current_date" == "$timestamp" ]]; then
            # Update the usage for this period
            if ! is_idle; then
                lines[$i]="$timestamp $((current_usage + SLEEP_TIME))"
            fi
            updated=true
            break
        fi
    done
    
    # If we didn't find an entry for this hour, add a new one
    if ! $updated; then
        if ! is_idle; then
            lines+=("$timestamp $SLEEP_TIME")
        else
            lines+=("$timestamp 0")
        fi
    fi
    
    # Write all lines to temporary file
    printf "%s\n" "date usage" > "$temp_file"
    printf "%s\n" "${lines[@]:1}" >> "$temp_file"
    
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
