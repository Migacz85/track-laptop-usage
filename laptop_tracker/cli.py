import click
import logging
import os
import signal
import subprocess
import time
import getpass
from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import psutil
from .tracker import LaptopTracker

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

def is_bash_tracker_running():
    """Check if bash tracker process is running"""
    try:
        output = subprocess.check_output(["pgrep", "-f", "track-laptop-usage.sh"]).decode().strip()
        return bool(output)
    except subprocess.CalledProcessError:
        return False
    
    def run_trackers():
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

    if not foreground:
        # Daemonize the process
        pid = os.fork()
        if pid > 0:
            # Parent process exits
            return
        # Child process continues
        run_trackers()
    else:
        run_trackers()

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
    daily_log_file = log_dir / "daily-laptop.log"
    
    daily_df = pd.read_csv(daily_log_file, sep=' ', engine='python', header=0)
    # Handle multiple timestamp formats
    daily_df['date'] = pd.to_datetime(
        daily_df['date'],
        format='mixed',
        dayfirst=False
    )
    daily_df['usage_hours'] = daily_df['usage'] / 3600
    daily_df['hour'] = daily_df['date'].dt.hour
    daily_df['day'] = daily_df['date'].dt.date
    
    # Ensure we have data for all hours
    daily_df['hour'] = daily_df['date'].dt.hour
    daily_df['day'] = daily_df['date'].dt.date
    
    # Create a complete grid of hours and days
    all_hours = pd.DataFrame({'hour': range(24)})
    all_days = pd.DataFrame({'day': daily_df['day'].unique()})
    complete_grid = all_days.assign(key=1).merge(all_hours.assign(key=1), on='key').drop('key', axis=1)
    
    # Merge with actual data
    merged_df = complete_grid.merge(daily_df, on=['day', 'hour'], how='left')
    merged_df['usage_hours'] = merged_df['usage_hours'].fillna(0)
    
    # Create heatmap data
    heatmap_data = merged_df.pivot_table(index='hour', columns='day', values='usage_hours', aggfunc='sum')
    
    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap='YlGnBu', cbar_kws={'label': 'Usage (hours)'}, vmin=0)
    plt.title('Hourly Usage Heatmap')
    plt.xlabel('Date')
    plt.ylabel('Hour of Day')
    plt.tight_layout()
    plt.show()

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
    
    # Read and parse the log file
    daily_df = pd.read_csv(daily_log_file, sep=' ', engine='python', header=0)
    
    # Handle mixed timestamp formats (daily and hourly)
    try:
        # First try parsing as hourly format
        daily_df['date'] = pd.to_datetime(
            daily_df['date'], 
            format='%Y/%m/%d %H',
            dayfirst=False
        )
    except ValueError:
        try:
            # Fall back to daily format
            daily_df['date'] = pd.to_datetime(
                daily_df['date'], 
                format='%Y/%m/%d',
                dayfirst=False
            )
        except ValueError:
            logger.error("Could not parse log file timestamps")
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
            print(f"{row['date_str']}: {time_str}")

if __name__ == "__main__":
    cli()
