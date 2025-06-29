import click
import logging
import os
import signal
import subprocess
import time
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
    """Laptop Usage Tracker"""
    pass

@cli.command()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--daemon', is_flag=True, help='Run as daemon in background')
def start(debug, daemon):
    """Start tracking laptop usage"""
    # Set log level
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if LaptopTracker.is_running():
        logging.warning("Tracker is already running")
        return
    
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
            
            if not daemon:
                # Keep the main process running if not daemon
                while True:
                    time.sleep(1)
            
        except Exception as e:
            logging.error(f"Error starting tracker: {e}")
            raise click.Abort()

    if daemon:
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
@click.option('--debug', is_flag=True, help='Enable debug logging')
def stop(debug):
    """Stop tracking laptop usage"""
    # Set log level
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Stop Python trackers
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower() and \
               'laptop_tracker' in ' '.join(proc.info['cmdline'] or []):
                logging.debug(f"Stopping tracker process {proc.info['pid']}")
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Stop bash trackers (legacy)
    try:
        output = subprocess.check_output(["pgrep", "-f", "track-laptop-usage.sh"]).decode().strip()
        if output:
            for pid in output.split('\n'):
                try:
                    logging.debug(f"Stopping bash tracker process {pid}")
                    os.kill(int(pid), signal.SIGTERM)
                except ProcessLookupError:
                    continue
            logging.info("Tracker stopped (killed PIDs: %s)", output.replace('\n', ', '))
        else:
            logging.info("No tracker process found")
    except subprocess.CalledProcessError:
        logging.info("No tracker process found")

@cli.command()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--daemon', is_flag=True, help='Run as daemon in background')
def restart(debug, daemon):
    """Restart tracking laptop usage"""
    stop(debug=debug)
    time.sleep(1)  # Give it a moment to stop
    start(debug=debug, daemon=daemon)

@cli.command()
def status():
    """Check if tracker is running"""
    try:
        output = subprocess.check_output(["pgrep", "-f", "track-laptop-usage.sh"]).decode().strip()
        if output:
            print("Tracker is running (PID(s):", output.replace('\n', ', '), ")")
        else:
            print("Tracker is not running")
    except subprocess.CalledProcessError:
        print("Tracker is not running")

@cli.command()
def daily():
    """Show daily usage chart"""
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
def hourly():
    """Show hourly usage heatmap"""
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
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--daily', is_flag=True, help='Show daily usage summary')
@click.option('--hour', is_flag=True, help='Show hourly usage details')
def logs(debug, daily, hour):
    """Show usage data - daily summary or hourly details"""
    # Set log level
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    log_dir = Path(__file__).parent.parent / "log"
    daily_log_file = log_dir / "daily-laptop.log"
    
    if not daily_log_file.exists():
        print("No log file found")
        return
    
    # Read and parse the log file
    daily_df = pd.read_csv(daily_log_file, sep=' ', engine='python', header=0)
    # Handle mixed timestamp formats (daily and hourly)
    daily_df['date'] = pd.to_datetime(
        daily_df['date'], 
        format='mixed',
        dayfirst=False
    )
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
        daily_df['date_str'] = daily_df['date'].dt.strftime('%Y/%m/%d %H:00')
        
        print("Hourly Usage Details")
        print("-" * 40)
        for _, row in daily_df.iterrows():
            hours = int(row['usage_hours'])
            mins = int((row['usage_hours'] - hours) * 60)
            print(f"{row['date_str']}: {hours}h {mins}m")

if __name__ == "__main__":
    cli()
