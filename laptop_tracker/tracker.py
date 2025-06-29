import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path
import psutil
import signal
import sys

class LaptopTracker:
    def __init__(self, track_type='daily', log_dir='log'):
        self.track_type = track_type
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / f"{track_type}-laptop.log"
        self.idle_threshold = 120  # seconds
        self.update_interval = 60  # seconds
        self.running = False
        
        # Setup logging
        self.log_dir.mkdir(exist_ok=True)
        self._init_log_file()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _init_log_file(self):
        """Initialize log file with header if it doesn't exist"""
        if not self.log_file.exists():
            with open(self.log_file, 'w') as f:
                f.write("date usage\n")
            self._log_entry(0)  # Initialize with 0 usage

    def _get_timestamp(self):
        """Get current timestamp based on track type"""
        now = datetime.now()
        if self.track_type == 'daily':
            return now.strftime('%Y/%m/%d')
        elif self.track_type == 'hourly':
            return now.strftime('%Y/%m/%d %H')
        elif self.track_type == 'minutes':
            return now.strftime('%Y/%m/%d %H:%M')
        else:
            raise ValueError(f"Invalid track type: {self.track_type}")

    def _is_idle(self):
        """Check if user is idle using multiple methods"""
        try:
            # Method 1: Check X11 idle time (for GUI sessions)
            try:
                idle_ms = int(subprocess.check_output(['xprintidle']).decode().strip())
                idle_sec = idle_ms / 1000
                if idle_sec > self.idle_threshold:
                    return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
                
            # Method 2: Check console idle time (for terminal sessions)
            try:
                who_output = subprocess.check_output(['who', '-u']).decode().strip()
                if who_output:
                    idle_str = who_output.splitlines()[0].split()[4]  # Get idle time from first session
                    if idle_str == '.':
                        return False  # Active if idle time is '.'
                    idle_sec = int(idle_str.split(':')[0]) * 60 + int(idle_str.split(':')[1])
                    if idle_sec > self.idle_threshold:
                        return True
            except (subprocess.CalledProcessError, ValueError, IndexError):
                pass
                
            # Method 3: Fallback to /proc/uptime
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime, idle_time = map(float, f.read().split())
                if idle_time > self.idle_threshold:
                    return True
            except Exception:
                pass
                
            # If none of the methods detected idle, assume active
            return False
            
        except Exception as e:
            logging.warning(f"Could not check idle time: {e}")
            return False

    def _log_entry(self, usage):
        """Add or update log entry for current period"""
        timestamp = self._get_timestamp()
        lines = []
        updated = False

        logging.debug(f"Updating log for {timestamp} with {usage}s")

        # Read existing log entries
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            logging.debug(f"Found {len(lines)} existing log entries")

        # Process entries
        new_lines = []
        for line in lines[1:]:  # Skip header
            line = line.strip()
            if not line:
                continue
                
            log_timestamp, log_usage = line.rsplit(' ', 1)
            if log_timestamp == timestamp:
                # Update existing entry
                new_lines.append(f"{timestamp} {int(log_usage) + usage}\n")
                updated = True
            else:
                new_lines.append(f"{line}\n")

        # Add new entry if needed
        if not updated:
            new_lines.append(f"{timestamp} {usage}\n")

        # Write updated log
        with open(self.log_file, 'w') as f:
            f.write("date usage\n")
            f.writelines(new_lines)

    def _handle_signal(self, signum, frame):
        """Handle termination signals"""
        self.running = False
        logging.info("Received termination signal, shutting down...")
        sys.exit(0)

    def start(self):
        """Start the tracking loop"""
        self.running = True
        logging.info(f"Starting {self.track_type} tracking...")
        
        while self.running:
            if not self._is_idle():
                logging.debug(f"User active - adding {self.update_interval}s")
                self._log_entry(self.update_interval)
            else:
                logging.debug("User idle - skipping update")
            time.sleep(self.update_interval)

    @classmethod
    def is_running(cls):
        """Check if tracker is already running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower() and \
                   'laptop_tracker' in ' '.join(proc.info['cmdline'] or []):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False
