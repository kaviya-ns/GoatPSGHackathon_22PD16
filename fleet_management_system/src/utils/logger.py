import time
from datetime import datetime
from typing import Optional
import os

class FleetLogger:
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize the logger with an optional log file path.
        If no path is provided, defaults to 'logs/fleet_logs.txt'
        """
        self.log_file = log_file if log_file else self._get_default_log_path()
        self._ensure_log_directory_exists()
        
    def _get_default_log_path(self) -> str:
        return os.path.join("logs", "fleet_logs.txt")
    
    def _ensure_log_directory_exists(self):
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def log(self, message: str, print_to_console: bool = True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        
        if print_to_console:
            print(log_entry)
        
        self._write_to_file(log_entry)
    
    def _write_to_file(self, message: str):
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message + "\n")
        except IOError as e:
            print(f"Failed to write to log file: {e}")
    
    def log_robot_event(self, robot_id: int, event: str, details: str = ""):
        self.log(f"Robot {robot_id} {event}. {details}".strip())
    
    def log_system_event(self, event: str, details: str = ""):
        self.log(f"System {event}. {details}".strip())
    
    def clear_logs(self):
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("")
            self.log("Logs cleared by user request", False)
        except IOError as e:
            print(f"Failed to clear log file: {e}")