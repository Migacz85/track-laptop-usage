import warnings
import click
import logging
import os
import signal
import subprocess
import time
import getpass
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import psutil
from .tracker import LaptopTracker

# Suppress matplotlib warnings more aggressively
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

@click.group()
def cli():
    """
    Laptop Usage Tracker - Monitor and analyze your computer usage patterns.
    
    This tool tracks your active computer usage (excluding idle time) and provides:
    - Daily usage statistics and charts
    - Hourly usage heatmaps
    - Detailed usage logs
    
    Start tracking with 'laptop-tracker start' and view reports with:
    - 'laptop-tracker daily' for daily usage
    - 'laptop-tracker hourly' for hourly heatmaps
    - 'laptop-tracker logs' for detailed usage data
    
    Manage tracking with:
    - 'laptop-tracker status' to check if running
    - 'laptop-tracker stop' to stop tracking
    - 'laptop-tracker restart' to restart tracking
    """
    pass

@cli.command()
@click.option('--debug', is_flag=True, help='Enable verbose debug logging')
@click.option('--foreground', is_flag=True, help='Run in foreground (not as daemon)')
def start(debug, foreground):
    """
    Start tracking laptop usage.
    
    This will begin monitoring your activity and logging usage data.
    Runs as daemon by default unless --foreground is specified.
    """
    # Set log level
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Check for both Python and bash trackers
    if LaptopTracker.is_running() or is_bash_tracker_running():
        logging.warning("Tracker is already running")
        return

    # Verify dependencies
    try:
        subprocess.check_output(['xprintidle', '--version'])
        logging.debug("xprintidle is available")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error("xprintidle not found - idle detection won't work")
        logging.error("Please install xprintidle: sudo apt install xprintidle")
        return

    # Start trackers
    try:
        import multiprocessing
        
        def run_tracker(track_type):
            tracker = LaptopTracker(track_type=track_type)
            tracker.start()
        
        # Create separate processes for each tracker
        daily_process = multiprocessing.Process(
            target=run_tracker, 
            args=('daily',)
        )
        hourly_process = multiprocessing.Process(
            target=run_tracker,
            args=('hourly',)
        )
        
        # Start both processes
        daily_process.start()
        hourly_process.start()
        
        logging.info("Trackers are now running. Press Ctrl+C to stop.")
        
        # Keep main process running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down tracker...")
    except Exception as e:
        logging.error(f"Failed to start tracker: {e}")

def is_bash_tracker_running():
    """Check if bash tracker process is running"""
    try:
        output = subprocess.check_output(["pgrep", "-f", "track-laptop-usage.sh"]).decode().strip()
        return bool(output)
    except subprocess.CalledProcessError:
        return False
    
    def run_trackers(foreground):
        """Run all tracking processes with status logging"""
        logging.debug("Initializing tracking processes...")
        try:
            daily_tracker = LaptopTracker(track_type='daily')
            hourly_tracker = LaptopTracker(track_type='hourly')
            
            logging.info("Starting daily tracker...")
            daily_tracker.start()
            
            logging.info("Starting hourly tracker...")
            hourly_tracker.start()
            
        except Exception as e:
            logging.error(f"Failed to start trackers: {e}")
            raise
        try:
            import multiprocessing
            
            def run_tracker(track_type):
                tracker = LaptopTracker(track_type=track_type)
                tracker.start()
            
            # Create separate processes for each tracker
            daily_process = multiprocessing.Process(
                target=run_tracker, 
                args=('daily',)
            )
            hourly_process = multiprocessing.Process(
                target=run_tracker,
                args=('hourly',)
            )
            
            # Start both processes
            daily_process.start()
            hourly_process.start()
            
            if not foreground:
                # Keep the main process running if not foreground
                while True:
                    time.sleep(1)
            
        except Exception as e:
            logging.error(f"Error starting tracker: {e}")
            raise click.Abort()

    # Always run in foreground
    logging.info("Starting laptop tracker in foreground mode...")
    logging.debug("Checking system status...")
    
    # Verify dependencies
    try:
        subprocess.check_output(['xprintidle', '--version'])
        logging.debug("xprintidle is available")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.warning("xprintidle not found - idle detection may be limited")
    
    # Start trackers with status output
    logging.info("Starting tracking processes...")
    try:
        run_trackers(foreground=True)
        logging.info("Tracker is now running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)  # Keep main process alive
    except KeyboardInterrupt:
        logging.info("Shutting down tracker...")
    except Exception as e:
        logging.error(f"Tracker failed: {e}")

@cli.command()
def stop():
    """
    Stop tracking laptop usage.
    
    This will terminate any running tracker processes.
    """
    # Set log level
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Ensure we have a logger instance
    logger = logging.getLogger(__name__)

    # Stop Python trackers
    found = False
    current_pid = os.getpid()  # Don't kill our own process
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'username']):
        try:
            if proc.info['pid'] == current_pid:
                continue  # Skip our own process
                
            cmdline = ' '.join(proc.info['cmdline'] or [])
            username = proc.info['username']
            
            # Match both the Python process and our specific command
            if (('python' in proc.info['name'].lower() or 
                 'python3' in proc.info['name'].lower()) and 
                ('laptop_tracker' in cmdline or 
                 'laptop-tracker' in cmdline or
                 'track-laptop-usage.sh' in cmdline) and
                username == os.getlogin()):  # Only kill processes owned by current user
                
                logger.debug(f"Stopping tracker process {proc.info['pid']} - {cmdline}")
                proc.terminate()
                try:
                    proc.wait(timeout=5)  # Wait for process to terminate
                    found = True
                except psutil.TimeoutExpired:
                    logger.warning(f"Process {proc.info['pid']} did not terminate, killing it")
                    proc.kill()
                    found = True
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if not found:
        logger.debug("No Python tracker processes found")
    else:
        logger.info("Successfully stopped Python tracker processes")

    # Stop bash trackers (legacy)
    try:
        output = subprocess.check_output(["pgrep", "-f", "track-laptop-usage.sh"]).decode().strip()
        if output:
            pids = []
            for pid in output.split('\n'):
                try:
                    logger.debug(f"Stopping bash tracker process {pid}")
                    os.kill(int(pid), signal.SIGTERM)
                    pids.append(pid)
                except ProcessLookupError:
                    continue
            if pids:
                logger.info("Stopped bash tracker processes (PIDs: %s)", ', '.join(pids))
            else:
                logger.info("No running bash tracker processes found")
        else:
            logger.info("No bash tracker processes found")
    except subprocess.CalledProcessError:
        logger.info("No bash tracker processes found")

@cli.command()
def restart():
    """
    Restart the laptop usage tracker.
    
    This will stop any running trackers and start new ones.
    """
    stop()
    time.sleep(1)  # Give it a moment to stop
    start()

@cli.command()
def status():
    """
    Check if the tracker is currently running.
    
    Displays the status of any active tracker processes.
    """
    # Set log level
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    running = False
    current_user = os.getlogin()
    
    # Check Python trackers
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'username']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            username = proc.info['username']
            
            if (('python' in proc.info['name'].lower() or 
                 'python3' in proc.info['name'].lower()) and 
                ('laptop_tracker' in cmdline or 
                 'laptop-tracker' in cmdline) and
                username == current_user):
                
                print(f"Python tracker running (PID: {proc.info['pid']})")
                running = True
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    # Check bash trackers
    try:
        output = subprocess.check_output(["pgrep", "-f", "track-laptop-usage.sh"]).decode().strip()
        if output:
            print(f"Bash tracker running (PID(s): {output.replace(chr(10), ', ')})")
            running = True
    except subprocess.CalledProcessError:
        pass
    
    if not running:
        print("Tracker is not running")

@cli.command()
def daily():
    """
    Show daily usage chart.
    
    Displays a bar chart of your daily computer usage over time.
    """
    # Set log level
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    logging.debug("Generating daily usage chart")
    log_dir = Path(__file__).parent.parent / "log"
    log_dir.mkdir(exist_ok=True)  # Ensure log directory exists
    daily_log_file = log_dir / "hourly-laptop.log"
    
    daily_df = pd.read_csv(daily_log_file, sep=' ', engine='python', header=0)
    # Handle multiple timestamp formats
    daily_df['date'] = pd.to_datetime(daily_df['date'], format='mixed')
    daily_df['usage_hours'] = daily_df['usage'] / 3600

    plt.figure(figsize=(12, 6))
    sns.barplot(data=daily_df, x='date', y='usage_hours', color='skyblue')
    plt.title('Daily Laptop Usage (hours)')
    plt.xlabel('Date')
    plt.ylabel('Usage (hours)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

@cli.command()
def hourly():
    """
    Show hourly usage heatmap.
    
    Displays a heatmap visualization of your computer usage by hour.
    """
    # Set log level
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    logging.debug("Generating hourly usage heatmap")
    log_dir = Path(__file__).parent.parent / "log"
    log_dir.mkdir(exist_ok=True)  # Ensure log directory exists
    daily_log_file = log_dir / "hourly-laptop.log"
    
    # Read and parse the log file with consistent timestamp handling
    try:
        # First print raw file contents
        print("\nRaw log file contents:")
        with open(daily_log_file, 'r') as f:
            print(f.read())
            
        # Now process the data
        data = []
        with open(daily_log_file, 'r') as f:
            for line in f.readlines()[1:]:  # Skip header
                line = line.strip()
                if not line:
                    continue
                    
                # Split on last space only (handles timestamps with spaces)
                parts = line.rsplit(' ', 1)
                if len(parts) != 2:
                    print(f"Skipping malformed line (missing parts): {line}")
                    continue
                        
                timestamp, usage = parts[0], parts[1]
                    
                try:
                    usage = int(usage)
                        
                    # Standardize timestamp format - replace | with space
                    timestamp = timestamp.replace('|', ' ')
                    print(f"\nProcessing line: {line}")
                    print(f"Parsed timestamp: {timestamp}")
                    print(f"Parsed usage: {usage}")
                        
                    # Parse into datetime object
                    if ' ' in timestamp:  # Has hour component
                        date_str, hour_str = timestamp.split(' ')
                        hour = int(hour_str.split(':')[0])
                        date_obj = pd.to_datetime(date_str).replace(hour=hour)
                        print(f"Parsed as datetime with hour: {date_obj}")
                    else:  # Date only
                        date_obj = pd.to_datetime(timestamp)
                        hour = 0
                        print(f"Parsed as date only: {date_obj}")
                            
                    data.append({
                        'date': date_obj,
                        'hour': hour, 
                        'usage': usage,
                        'day': date_obj.date()  # Add date-only column
                    })
                    print(f"Added data point: {data[-1]}")
                except ValueError as e:
                    print(f"Error parsing line: {line} - {e}")
                    continue
            
        if not data:
            print("No valid data found in log file")
            return
                
        daily_df = pd.DataFrame(data)
        # Convert usage to minutes for annotations
        daily_df['usage_minutes'] = daily_df['usage'] / 60
        daily_df['usage_hours'] = daily_df['usage'] / 3600
        
        # Print parsed DataFrame
        print("\nParsed DataFrame:")
        print(daily_df)
        print("\nDataFrame info:")
        print(daily_df.info())
        print("\nDataFrame describe:")
        print(daily_df.describe())
        
        # Ensure we have datetime types
        daily_df['day'] = pd.to_datetime(daily_df['day'])
        
        # Create complete grid only for days we have data
        unique_days = daily_df['day'].unique()
        all_hours = pd.DataFrame({'hour': range(24)})
        all_days = pd.DataFrame({'day': unique_days})
        complete_grid = all_days.assign(key=1).merge(all_hours.assign(key=1), on='key').drop('key', axis=1)
        
        # Merge with actual data
        merged_df = complete_grid.merge(
            daily_df[['day', 'hour', 'usage_hours']],
            on=['day', 'hour'],
            how='left'
        ).fillna(0)
        
        # Print merged DataFrame details
        print("\nMerged DataFrame:")
        print(merged_df)
        print("\nMerged DataFrame info:")
        print(merged_df.info())
        print("\nMerged DataFrame describe:")
        print(merged_df.describe())
        
        # Ensure we have complete 24-hour data for each day
        merged_df = merged_df.sort_values(['day', 'hour'])
        
        # Create heatmap data - ensure proper alignment
        heatmap_data = merged_df.pivot_table(
            index='hour',
            columns='day',
            values='usage_hours',  # Use hours for color scaling
            aggfunc='sum',
            fill_value=0
        ).astype(float)  # Ensure numeric type
        
        # Create annotation data with minutes
        annot_data = merged_df.pivot_table(
            index='hour',
            columns='day',
            values='usage_minutes',  # Use minutes for annotations
            aggfunc='sum',
            fill_value=0
        ).astype(float)
        
        # Ensure all 24 hours are represented in correct order
        heatmap_data = heatmap_data.reindex(range(24), fill_value=0)
        
        # Sort columns chronologically
        heatmap_data = heatmap_data[sorted(heatmap_data.columns)]
        
        # Create date range based on actual data
        if len(heatmap_data.columns) > 0:
            start_date = min(heatmap_data.columns)
            end_date = max(heatmap_data.columns)
            date_range = pd.date_range(start=start_date, end=end_date)
            
            # Add missing days with empty data
            missing_dates = [d for d in date_range if d not in heatmap_data.columns]
            for date in missing_dates:
                heatmap_data[date] = 0
            # Re-sort columns
            heatmap_data = heatmap_data[sorted(heatmap_data.columns)]
        
        # Print essential debug info
        print("\nEssential Debug Info:")
        print(f"Total entries: {len(daily_df)}")
        print(f"Date range: {daily_df['date'].min()} to {daily_df['date'].max()}")
        print(f"Total usage hours: {daily_df['usage_hours'].sum():.1f}")
        print(f"Heatmap dimensions: {heatmap_data.shape}")
        
        # Apply linear scaling with adjusted vmax
        max_val = heatmap_data.max().max()
        if max_val > 0:
            # Set vmax to 90th percentile to make patterns more visible
            vmax = np.percentile(heatmap_data.values, 90)
            if vmax == 0:  # Fallback if all values are same
                vmax = max_val
        else:
            vmax = 1
        
        # Configure color scaling with 100 distinct levels
        max_val = heatmap_data.max().max()
        if max_val > 0:
            # Use the maximum value as the darkest color
            vmax = max_val
            # Ensure we have at least 100 distinct color levels
            if vmax < 1:
                vmax = 1  # Minimum range for 100 levels
        else:
            # Default scale if no data
            vmax = 1
            
        # Set vmin to 0 to ensure consistent baseline
        vmin = 0
        
        # Create custom color map with 100 distinct levels
        cmap = sns.color_palette("YlGnBu", n_colors=100, as_cmap=True)

        # Print essential heatmap info
        print("\nHeatmap Summary:")
        print(f"Date Range: {heatmap_data.columns[0]} to {heatmap_data.columns[-1]}")
        print(f"Total Usage: {heatmap_data.sum().sum():.1f} hours")
        print(f"Busiest Hour: {heatmap_data.sum(axis=1).idxmax()}:00")
        
        plt.figure(figsize=(16, 8))
        ax = sns.heatmap(
            heatmap_data,
            cmap=cmap,
            cbar_kws={
                'label': 'Usage (hours)',
                'orientation': 'horizontal',
                'pad': 0.1,
                'ticks': [0, vmax/2, vmax],
                'shrink': 0.8  # Make colorbar slightly smaller
            },
            vmin=vmin,
            vmax=vmax,
            square=True,
            linewidths=0.3,
            linecolor='white',
            annot=annot_data,  # Use minutes for annotations
            fmt=".0f",
            annot_kws={
                'fontsize': 8,
                'color': 'white',
                'alpha': 0.9,
                'fontweight': 'bold'
            },
            norm=plt.Normalize(vmin, vmax)  # Ensure 100 distinct levels
        )
        
        # Format x-axis dates to be more readable
        date_labels = [pd.to_datetime(col).strftime('%m/%d') for col in heatmap_data.columns]
        ax.set_xticks(range(len(date_labels)))
        ax.set_xticklabels(date_labels, rotation=45, ha='right')
        
        # Format y-axis hours - horizontal labels
        ax.set_yticks(range(24))
        ax.set_yticklabels([f"{h:02d}:00" for h in range(24)], rotation=0)
        
        # Add grid lines for better readability
        ax.hlines(range(24), *ax.get_xlim(), colors='white', linewidth=0.5)
        ax.vlines(range(len(date_labels)), *ax.get_ylim(), colors='white', linewidth=0.5)
        
        plt.title('Hourly Usage Heatmap')
        plt.xlabel('Date (MM/DD)')
        plt.ylabel('Hour of Day')
        plt.tight_layout()
        plt.show()
        
    except pd.errors.EmptyDataError:
        logging.warning("Log file is empty")
        print("No usage data available to display")
    except Exception as e:
        logging.error(f"Error generating heatmap: {e}")
        print("Failed to generate heatmap. Check logs for details.")

@cli.command()
@click.option('--daily', is_flag=True, help='Show daily usage summary')
@click.option('--hour', is_flag=True, help='Show hourly usage details')
def logs(daily, hour):
    """
    Show usage data - daily summary or hourly details.
    
    Displays detailed usage statistics in text format.
    Use --daily for daily summaries or --hour for hourly breakdowns.
    """
    # Set log level and get logger
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)
    
    log_dir = Path(__file__).parent.parent / "log"
    daily_log_file = log_dir / "daily-laptop.log"
    
    if not daily_log_file.exists():
        print("No log file found")
        return
    
    # Read and parse the log file with more flexible handling
    try:
        # Read log file with more robust parsing
        with open(daily_log_file, 'r') as f:
            lines = f.readlines()
            
        # Skip header and process lines manually
        data = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.rsplit(' ', 1)  # Split on last space only
            if len(parts) == 2:
                try:
                    # Convert usage to integer
                    usage = int(parts[1])
                    timestamp = parts[0]
                    
                    # Handle different timestamp formats
                    if '|' in timestamp:  # Heatmap format
                        date_part, time_part = timestamp.split('|')
                        if ':' in time_part:  # Minutes format
                            hour, minute = time_part.split(':')
                            parsed_date = datetime.strptime(f"{date_part} {hour}:{minute}", "%Y/%m/%d %H:%M")
                        else:  # Hourly format
                            parsed_date = datetime.strptime(f"{date_part} {time_part}:00", "%Y/%m/%d %H:%M")
                    else:  # Daily format
                        parsed_date = datetime.strptime(timestamp, "%Y/%m/%d")
                    
                    data.append([timestamp, parsed_date, usage])
                except ValueError as e:
                    logging.warning(f"Skipping malformed line: {line} - {e}")
                    continue
            
        daily_df = pd.DataFrame(data, columns=['raw_date', 'date', 'usage'])
        daily_df['usage'] = pd.to_numeric(daily_df['usage'], errors='coerce')
            
        if daily_df['date'].isna().any():
            logger.error("Could not parse timestamps - invalid format in log file")
            logger.debug(f"Problematic timestamps: {daily_df[daily_df['date'].isna()]['date']}")
            return
            
        logger.debug("Successfully parsed log file timestamps")
            
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return
    daily_df['usage_hours'] = daily_df['usage'] / 3600
    
    # Default to daily if no option specified
    if not daily and not hour:
        daily = True
    
    if daily:
        # Group by date for daily summary
        daily_df['day'] = daily_df['date'].dt.date
        daily_summary = daily_df.groupby('day')['usage_hours'].sum().reset_index()
        
        print("Daily Usage Summary")
        print("-" * 40)
        for _, row in daily_summary.iterrows():
            date_str = row['day'].strftime('%Y/%m/%d')
            hours = int(row['usage_hours'])
            mins = int((row['usage_hours'] - hours) * 60)
            print(f"{date_str}: {hours}h {mins}m")
    
    if hour:
        # Show hourly details
        daily_df['hour'] = daily_df['date'].dt.hour
        # Format date string based on whether timestamps contain hour info
        if any(' ' in str(date) for date in daily_df['date']):
            daily_df['date_str'] = daily_df['date'].dt.strftime('%Y/%m/%d %H:00')
        else:
            daily_df['date_str'] = daily_df['date'].dt.strftime('%Y/%m/%d') + ' 00:00'
        
        print("Hourly Usage Details")
        print("-" * 40)
        for _, row in daily_df.iterrows():
            hours = int(row['usage_hours'])
            mins = int((row['usage_hours'] - hours) * 60)
            # Format time nicely with leading zeros
            time_str = f"{hours:02d}:{mins:02d}"
            
            # Directly use components from parsed datetime
            hour = row['date'].hour
            date_str = row['date'].strftime('%Y/%m/%d')
            logging.debug(f"Displaying entry: date={date_str} hour={hour}")
            
            print(f"{date_str} {hour:02d}:00 - {time_str}")

if __name__ == "__main__":
    cli()
