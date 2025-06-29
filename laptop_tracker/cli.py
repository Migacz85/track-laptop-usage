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
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@click.group()
def cli():
    """
    Track and analyze laptop usage patterns.
    
    This tool monitors your active computer usage and provides detailed
    reports and visualizations of your daily and hourly activity.
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
@click.option('--debug', is_flag=True, help='Enable verbose debug logging')
def stop(debug):
    """
    Stop tracking laptop usage.
    
    This will terminate any running tracker processes.
    """
    # Set log level
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
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
@click.option('--debug', is_flag=True, help='Enable verbose debug logging')
@click.option('--foreground', is_flag=True, help='Run in foreground (not as daemon)')
def restart(debug, foreground):
    """
    Restart the laptop usage tracker.
    
    This will stop any running trackers and start new ones.
    Runs as daemon by default unless --foreground is specified.
    """
    stop(debug=debug)
    time.sleep(1)  # Give it a moment to stop
    start(debug=debug, foreground=foreground)

@cli.command()
def status():
    """
    Check if the tracker is currently running.
    
    Displays the status of any active tracker processes.
    """
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
@click.option('--debug', is_flag=True, help='Enable verbose debug logging')
def daily(debug):
    """
    Show daily usage chart.
    
    Displays a bar chart of your daily computer usage over time.
    """
    # Set log level
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
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
@click.option('--debug', is_flag=True, help='Enable verbose debug logging')
def hourly(debug):
    """
    Show hourly usage heatmap.
    
    Displays a heatmap visualization of your computer usage by hour.
    """
    # Set log level
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logging.debug("Generating hourly usage heatmap")
    log_dir = Path(__file__).parent.parent / "log"
    log_dir.mkdir(exist_ok=True)  # Ensure log directory exists
    daily_log_file = log_dir / "hourly-laptop.log"
    
    # Read and parse the log file with consistent timestamp handling
    try:
        data = []
        with open(daily_log_file, 'r') as f:
            for line in f.readlines()[1:]:  # Skip header
                line = line.strip()
                if not line:
                    continue
                    
                # Split on last space only (handles timestamps with spaces)
                parts = line.rsplit(' ', 1)
                if len(parts) != 2:
                    continue
                        
                timestamp, usage = parts[0], parts[1]
                    
                try:
                    usage = int(usage)
                        
                    # Standardize timestamp format - replace | with space
                    timestamp = timestamp.replace('|', ' ')
                        
                    # Parse into datetime object
                    if ' ' in timestamp:  # Has hour component
                        date_str, hour_str = timestamp.split(' ')
                        hour = int(hour_str.split(':')[0])
                        date_obj = pd.to_datetime(date_str).replace(hour=hour)
                    else:  # Date only
                        date_obj = pd.to_datetime(timestamp)
                        hour = 0
                            
                    data.append({
                        'date': date_obj,
                        'hour': hour, 
                        'usage': usage,
                        'day': date_obj.date()  # Add date-only column
                    })
                except ValueError as e:
                    logging.warning(f"Skipping malformed line: {line} - {e}")
                    continue
            
        if not data:
            logging.warning("No valid data found in log file")
            print("No usage data available to display")
            return
                
        daily_df = pd.DataFrame(data)
        daily_df['usage_hours'] = daily_df['usage'] / 3600
        
        # Debug output to verify data
        logging.debug(f"Found {len(daily_df)} log entries")
        logging.debug("Sample data:")
        logging.debug(daily_df.head())
        
        # Ensure we have datetime types
        daily_df['day'] = pd.to_datetime(daily_df['day'])
        
        # Create complete grid for past 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=29)
        date_range = pd.date_range(start_date, end_date, freq='D')
        
        all_hours = pd.DataFrame({'hour': range(24)})
        all_days = pd.DataFrame({'day': date_range.date})  # Convert to date objects
        complete_grid = all_days.assign(key=1).merge(all_hours.assign(key=1), on='key').drop('key', axis=1)
        
        # Ensure daily_df['day'] is date type for merge
        daily_df['day'] = pd.to_datetime(daily_df['day']).dt.date
        
        # Convert daily_df['day'] to date type for proper merging
        daily_df['day'] = pd.to_datetime(daily_df['day']).dt.date
        
        # Merge with actual data, preserving all hours
        merged_df = complete_grid.merge(
            daily_df[['day', 'hour', 'usage_hours']],
            on=['day', 'hour'],
            how='left'
        )
        
        # Fill missing values with 0 but keep original usage values
        merged_df['usage_hours'] = merged_df['usage_hours'].fillna(0)
        
        # Debug output to verify merged data
        logging.debug("Merged data preview:")
        logging.debug(merged_df.head())
        
        # Ensure we have exactly 30 days worth of data
        merged_df = merged_df[merged_df['day'].isin(date_range)]
        
        # Create heatmap data - ensure proper alignment
        heatmap_data = merged_df.pivot_table(
            index='hour',
            columns='day',
            values='usage_hours',
            aggfunc='sum',
            fill_value=0
        ).astype(float)  # Ensure numeric type
        
        # Ensure all 24 hours are represented in correct order
        heatmap_data = heatmap_data.reindex(range(24), fill_value=0)
        
        # Sort columns chronologically and ensure we have 30 days
        heatmap_data = heatmap_data[sorted(heatmap_data.columns)]
        if len(heatmap_data.columns) < 30:
            # Add missing days with empty data
            missing_dates = [d for d in date_range if d not in heatmap_data.columns]
            for date in missing_dates:
                heatmap_data[date] = 0
            # Re-sort columns
            heatmap_data = heatmap_data[sorted(heatmap_data.columns)]
        
        # Debug output to verify heatmap data
        logging.debug("Heatmap data preview:")
        logging.debug(heatmap_data.head())
        
        # Apply linear scaling with adjusted vmax
        max_val = heatmap_data.max().max()
        if max_val > 0:
            # Set vmax to 90th percentile to make patterns more visible
            vmax = np.percentile(heatmap_data.values, 90)
            if vmax == 0:  # Fallback if all values are same
                vmax = max_val
        else:
            vmax = 1
        
        # Debug output to verify heatmap data
        logging.debug("Heatmap data preview:")
        logging.debug(heatmap_data.head())
        
        plt.figure(figsize=(16, 8))
        ax = sns.heatmap(
            heatmap_data,
            cmap='YlGnBu',
            cbar_kws={'label': 'Usage (hours)'},
            vmin=0,
            vmax=vmax,
            square=True,
            linewidths=0.3,
            linecolor='white',
            annot=False
        )
        
        # Format x-axis dates to be more readable
        date_labels = [pd.to_datetime(col).strftime('%m/%d') for col in heatmap_data.columns]
        ax.set_xticks(range(len(date_labels)))
        ax.set_xticklabels(date_labels, rotation=45, ha='right')
        
        # Format y-axis hours
        ax.set_yticks(range(24))
        ax.set_yticklabels([f"{h:02d}:00" for h in range(24)])
        
        # Add grid lines for better readability
        ax.hlines(range(24), *ax.get_xlim(), colors='white', linewidth=0.5)
        ax.vlines(range(len(date_labels)), *ax.get_ylim(), colors='white', linewidth=0.5)
        
        plt.title('Hourly Usage Heatmap (Past 30 Days)')
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
@click.option('--debug', is_flag=True, help='Enable verbose debug logging')
@click.option('--daily', is_flag=True, help='Show daily usage summary')
@click.option('--hour', is_flag=True, help='Show hourly usage details')
def logs(debug, daily, hour):
    """
    Show usage data - daily summary or hourly details.
    
    Displays detailed usage statistics in text format.
    Use --daily for daily summaries or --hour for hourly breakdowns.
    """
    # Set log level and get logger
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
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
                    parts[1] = int(parts[1])
                    # Store both raw and parsed timestamps
                    # Parse components directly from raw string
                    if ' ' in parts[0] and ':' in parts[0]:
                        date_part, time_part = parts[0].split(' ')
                        year, month, day = date_part.split('/')
                        hour, minute = time_part.split(':')
                        parsed_date = datetime(
                            year=int(year),
                            month=int(month),
                            day=int(day),
                            hour=int(hour),
                            minute=int(minute)
                        )
                        data.append([parts[0], parsed_date, parts[1]])
                    else:
                        logging.warning(f"Skipping malformed timestamp: {parts[0]}")
                except ValueError:
                    logging.warning(f"Skipping malformed line: {line}")
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
