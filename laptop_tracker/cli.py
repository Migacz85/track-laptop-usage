import click
from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

@click.group()
def cli():
    """Laptop Usage Tracker"""
    pass

@cli.command()
def track():
    """Start tracking laptop usage"""
    from subprocess import Popen
    script_path = Path(__file__).parent.parent / "bin" / "track-laptop-usage.sh"
    Popen([str(script_path), "daily", "daily-laptop.log"])

@cli.command()
def show():
    """Show usage charts"""
    # Your existing chart.py logic here
    daily_log_file = Path.home() / "git" / "track-laptop-usage" / "log" / "daily-laptop.log"
    
    daily_df = pd.read_csv(daily_log_file, sep=' ', engine='python', header=0)
    daily_df['date'] = pd.to_datetime(daily_df['date'], format='%Y/%m/%d')
    daily_df['usage_hours'] = daily_df['usage'] / 3600

    plt.figure(figsize=(10, 5))
    sns.barplot(data=daily_df, x='date', y='usage_hours', color='skyblue')
    plt.title('Daily Laptop Usage (hours)')
    plt.xlabel('Date')
    plt.ylabel('Usage (hours)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    cli()
