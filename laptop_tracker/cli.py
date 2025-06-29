import click
import os
import signal
import subprocess
import time
from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

@click.group()
def cli():
    """Laptop Usage Tracker"""
    pass

def get_tracker_pid():
    """Get PID of running tracker process"""
    try:
        output = subprocess.check_output(["pgrep", "-f", "track-laptop-usage.sh"]).decode().strip()
        if not output:
            return None
        # Get the newest PID (last one in the list)
        pids = [int(pid) for pid in output.split('\n')]
        return pids[-1]
    except subprocess.CalledProcessError:
        return None

@cli.command()
def start():
    """Start tracking laptop usage"""
    script_path = Path(__file__).parent.parent / "bin" / "track-laptop-usage.sh"
    log_dir = Path(__file__).parent.parent / "log"
    log_dir.mkdir(exist_ok=True)
    
    if get_tracker_pid():
        print("Tracker is already running")
        return
    
    # Start in background with nohup
    subprocess.Popen(
        ["nohup", str(script_path), "daily", "daily-laptop.log"],
        stdout=open('/dev/null', 'w'),
        stderr=open('/dev/null', 'w'),
        preexec_fn=os.setpgrp
    )
    print("Tracker started")

@cli.command()
def stop():
    """Stop tracking laptop usage"""
    try:
        output = subprocess.check_output(["pgrep", "-f", "track-laptop-usage.sh"]).decode().strip()
        if output:
            for pid in output.split('\n'):
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except ProcessLookupError:
                    continue
            print("Tracker stopped (killed PIDs:", output.replace('\n', ', '), ")")
        else:
            print("No tracker process found")
    except subprocess.CalledProcessError:
        print("No tracker process found")

@cli.command()
def restart():
    """Restart tracking laptop usage"""
    stop()
    time.sleep(1)  # Give it a moment to stop
    start()

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
    daily_log_file = log_dir / "daily-laptop.log"
    
    daily_df = pd.read_csv(daily_log_file, sep=' ', engine='python', header=0)
    daily_df['date'] = pd.to_datetime(daily_df['date'], format='%Y/%m/%d')
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
    daily_df['date'] = pd.to_datetime(daily_df['date'], format='%Y/%m/%d')
    daily_df['usage_hours'] = daily_df['usage'] / 3600
    daily_df['hour'] = daily_df['date'].dt.hour
    daily_df['day'] = daily_df['date'].dt.date
    
    heatmap_data = daily_df.pivot_table(index='hour', columns='day', values='usage_hours', aggfunc='sum')
    
    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap='YlGnBu', cbar_kws={'label': 'Usage (hours)'})
    plt.title('Hourly Usage Heatmap')
    plt.xlabel('Date')
    plt.ylabel('Hour of Day')
    plt.tight_layout()
    plt.show()

@cli.command()
@click.option('--daily', is_flag=True, help='Show daily usage summary')
@click.option('--hour', is_flag=True, help='Show hourly usage details')
def logs(daily, hour):
    """Show usage data - daily summary or hourly details"""
    log_dir = Path(__file__).parent.parent / "log"
    daily_log_file = log_dir / "daily-laptop.log"
    
    if not daily_log_file.exists():
        print("No log file found")
        return
    
    # Read and parse the log file
    daily_df = pd.read_csv(daily_log_file, sep=' ', engine='python', header=0)
    daily_df['date'] = pd.to_datetime(daily_df['date'], format='%Y/%m/%d')
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
        
        print("Hourly Usage Details")
        print("-" * 40)
        for _, row in daily_df.iterrows():
            date_str = row['date'].strftime('%Y/%m/%d %H:00')
            hours = int(row['usage_hours'])
            mins = int((row['usage_hours'] - hours) * 60)
            print(f"{date_str}: {hours}h {mins}m")

if __name__ == "__main__":
    cli()
