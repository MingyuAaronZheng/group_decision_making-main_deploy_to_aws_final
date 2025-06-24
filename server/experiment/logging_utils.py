import json
import os
from datetime import datetime
from django.conf import settings

def save_client_logs(logs_data):
    """
    Save client-side logs to a file with timestamp
    """
    try:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create a log file with current date
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(logs_dir, f'client_logs_{today}.log')
        
        # Prepare log entry
        timestamp = datetime.now().isoformat()
        log_entry = f"\n\n[{timestamp}] Client Logs from {logs_data.get('page', 'unknown')}:\n"
        log_entry += logs_data.get('logs', 'No logs received')
        
        # Append to log file
        with open(log_file, 'a') as f:
            f.write(log_entry)
            
        return True, "Logs saved successfully"
    except Exception as e:
        return False, str(e)
