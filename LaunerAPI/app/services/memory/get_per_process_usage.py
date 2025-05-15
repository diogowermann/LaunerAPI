import psutil
from collections import deque
import logging
from app.services.memory.store_in_database import store_per_process_daily, store_per_process_hourly, store_per_process_weekly
from datetime import datetime

# CONSTATNS
SECONDS_IN_MINUTE = 60
MINUTES_IN_HOUR = 60
THRESHOLD = 1.5
TOP_PROCESSES = 7
DAYS_IN_WEEK = 7

# GLOBAL VARS
logger = logging.getLogger(__name__)
per_process_minute_readings = {}
all_data = []
hourly_data = deque(maxlen=MINUTES_IN_HOUR) # Last 60 minutes of data
last_minute = None
last_hour = None
last_day = None
last_week = None

async def per_process_usage():
    global all_data, last_minute
    processes = get_processes()
    
    now = datetime.now()
    current_minute = now.minute
    for process in processes:
        pid = process['pid'] if 'pid' in process else process['name']
        if pid not in per_process_minute_readings:
            per_process_minute_readings[pid] = {
                'name': process['name'],
                'readings': deque(maxlen=SECONDS_IN_MINUTE)
            }
        per_process_minute_readings[pid]['readings'].append(process['memory_percent'])

    if last_minute is None:
        last_minute = current_minute
        return None

    if current_minute != last_minute:
        minute_averages = {}
        for pid, data in per_process_minute_readings.items():
            if data['readings']:
                avg = sum(data['readings']) / len(data['readings'])
                minute_averages[data['name']] = round(avg, 2)
        
        all_data.append(minute_averages)
        per_process_minute_readings.clear()
        last_minute = current_minute
        hourly_data.append([now.strftime("%H:%M"), average(all_data)])
        return hourly_data
    return None


def average(data):
    all_keys = set()
    for d in data:
        all_keys.update(d.keys())
    average = {}
    for key in all_keys:
        values = [d[key] for d in data if key in d]
        average[key] = round(sum(values) / len(values), 2)
    return average

def get_processes():
    processes = []
    other_processes = 0
    for process in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            processes.append(process.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    sorted_processes = sorted(processes, key=lambda p: p['memory_percent'], reverse=True)
    top_processes = sorted_processes[:TOP_PROCESSES]

    for proc in sorted_processes[TOP_PROCESSES:]:
        other_processes += proc['memory_percent']

    top_processes.append({"name": "Outros Processos", "memory_percent": other_processes, "pid": 0})

    return top_processes

async def get_data(db):
    """Collect and store current data in memory."""
    global last_hour, last_day, last_week

    collected = await per_process_usage()

    now = datetime.now()
    current_hour = now.hour
    current_day = now.day
    current_week = now.isocalendar()[1]

    if last_hour is None:
        last_hour = current_hour
    if last_day is None:
        last_day = current_day
    if last_week is None:
        last_week = current_week

    if current_hour != last_hour and collected:
        data = [entry[1] for entry in hourly_data]
        if data and await store_per_process_hourly(db, average(data)):
            last_hour = current_hour

    if current_day != last_day and collected:
        data = [entry[1] for entry in hourly_data]
        if data and await store_per_process_daily(db, average(data)):
            last_day = current_day

    if current_week != last_week and collected:
        data = [entry[1] for entry in hourly_data]
        if data and await store_per_process_weekly(db, average(data)):
            last_week = current_week

def return_data():
    return hourly_data