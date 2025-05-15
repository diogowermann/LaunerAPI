from app.services.cpu.get_total_usage import return_data as get_cpu_data
from app.services.memory.get_total_usage import return_data as get_memory_data
from collections import deque
from datetime import datetime
import logging

# CONSTANTS
MINUTES_IN_HOUR = 60

# GLOBAL VARS
total_data = deque(maxlen=60)
logger = logging.getLogger(__name__)
last_minute = None

def merge_monitoring_data():
    """Collect and store both CPU and Memory data."""
    global last_minute
    cpu = get_cpu_data()
    memory = get_memory_data()
    now = datetime.now()

    current_minute = now.minute
    if last_minute is None:
        last_minute = current_minute

    if last_minute != current_minute:    
        total_data.append({
            "time": now.strftime("%H:%M"),
            "cpu": cpu[-1] if cpu else 0,
            "memory": memory[-1] if memory else 0
        })
        last_minute = current_minute
        return total_data
    return list(total_data)
def return_data():
    return merge_monitoring_data()