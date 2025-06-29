import os
import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path
import psutil
import signal
import sys

class LaptopTracker:
    def __init__(self, track_type='daily', log_dir=None):
        self.track_type = track_type
        self.log_dir = Path(__file__).parent.parent / "log" if log_dir is None else Path(log_dir)
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
                logging.debug(f"X11 idle time: {idle_sec}s")
                if idle_sec > self.idle_threshold:
                    logging.debug("X11 idle time exceeds threshold")
                    return True
                return False  # Active if idle time is below threshold
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logging.warning(f"xprintidle not available: {e}")
                pass
                
            # Only use X11 idle detection since it's most reliable
            try:
                idle_ms = int(subprocess.check_output(['xprintidle']).decode().strip())
                idle_sec = idle_ms / 1000
                logging.debug(f"X11 idle time: {idle_sec}s")
                return idle_sec > self.idle_threshold
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logging.error(f"xprintidle not available - cannot detect idle state: {e}")
                return False  # Assume active if we can't detect idle state
            
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
        
        try:
            while self.running:
                is_idle = self._is_idle()
                logging.debug(f"Idle state: {is_idle}")
                if not is_idle:
                    logging.debug(f"User active - adding {self.update_interval}s")
                    self._log_entry(self.update_interval)
                else:
                    logging.debug(f"User idle for {self.idle_threshold}+ seconds - skipping update")
                time.sleep(self.update_interval)
        except KeyboardInterrupt:
            logging.info(f"Stopping {self.track_type} tracker...")
            self.running = False

    @classmethod
    def is_running(cls):
        """Check if tracker is already running"""
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'username']):
            try:
                if proc.info['pid'] == current_pid:
                    continue  # Skip our own process
                    
                if ('python' in proc.info['name'].lower() or 
                    'python3' in proc.info['name'].lower()) and \
                   ('laptop_tracker' in ' '.join(proc.info['cmdline'] or []) or
                    'laptop-tracker' in ' '.join(proc.info['cmdline'] or [])) and \
                   proc.info['username'] == os.getlogin():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False
