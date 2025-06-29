# Laptop Usage Tracker

![Hourly Usage Heatmap](https://i.imgur.com/FTpKIK1.png)

Track and visualize your computer usage patterns with this lightweight Python tool.

## Key Features

- **Automatic tracking** of active computer time (excluding idle periods)
- **Hourly heatmap** showing usage patterns (darker colors = more usage)
- **Daily usage charts** for quick overviews
- **Lightweight** background process with minimal system impact

## What the Heatmap Shows

- **X-axis**: Dates (MM/DD)
- **Y-axis**: Hours of the day (00:00 to 23:00)  
- **Color intensity**: Usage time in hours (darker = more usage)

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start tracking:
```bash
laptop-tracker start
```

3. View your usage:
```bash
# Hourly heatmap
laptop-tracker hourly

# Daily usage chart  
laptop-tracker daily

# Raw usage data
laptop-tracker logs
```

## Usage Examples

Track your most productive hours:
```bash
laptop-tracker hourly --debug
```

See daily totals for the past month:
```bash 
laptop-tracker daily
```

Check if tracker is running:
```bash
laptop-tracker status
```

## Requirements

- Python 3.6+
- Linux (for idle detection)
- xprintidle (`sudo apt install xprintidle`)

## How It Works

1. Tracks active time (excluding idle periods >2 minutes)
2. Logs usage to `log/hourly-laptop.log`
3. Generates visualizations on demand

Perfect for:
- Productivity tracking
- Work habit analysis  
- Digital wellbeing awareness
