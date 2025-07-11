#!/bin/bash
set -e

echo "Installing system dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv
echo "Installing xprintidle (required for idle detection)..."
sudo apt-get update
sudo apt-get install -y libxss-dev xprintidle
echo -e "\nTesting xprintidle..."
xprintidle
if [ $? -ne 0 ]; then
    echo "ERROR: xprintidle not working properly!"
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing Python package..."
pip install -e .

echo "Creating log directory..."
mkdir -p log

echo "Installation complete!"
echo "To start tracking, run: laptop-tracker start"
echo "To view daily chart: laptop-tracker daily"
echo "To view hourly heatmap: laptop-tracker hourly"

