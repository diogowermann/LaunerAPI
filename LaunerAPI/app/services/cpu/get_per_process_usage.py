import psutil
from collections import deque
import logging
from app.services.cpu.store_in_database import (
    store_per_process_daily,
    store_per_process_hourly,
    store_per_process_weekly
)
from datetime import datetime

# CONSTANTS
SECONDS_IN_MINUTE = 60
MINUTES_IN_HOUR = 60
THRESHOLD = 1.5
TOP_PROCESSES = 7
DAYS_IN_WEEK = 7
CPU_COUNT = psutil.cpu_count()

# GLOBAL VARS
logger = logging.getLogger(__name__)
per_process_minute_readings = {}
all_data = []
hourly_data = deque(maxlen=MINUTES_IN_HOUR)  # Last 60 minutes of data
last_minute = None
last_hour = None
last_day = None
last_week = None
per_appserver_service_minute_readings = {}
appserver_service_hourly_data = deque(maxlen=MINUTES_IN_HOUR)
last_service_minute = None

# ----- Utility Functions -----
def average(data):
    all_keys = set()
    for d in data:
        all_keys.update(d.keys())
    avg = {}
    for key in all_keys:
        values = [d[key] for d in data if key in d]
        avg[key] = round(sum(values) / len(values), 2)
    return avg


# ----- Process-based usage -----
def get_processes():
    processes = []
    other_processes = 0
    protheus_services = 0
    for proc in psutil.process_iter(['name', 'cpu_percent']):
        try:
            info = proc.info
            if info['name'].lower() == "system idle process":
                continue

            info['cpu_percent'] = info['cpu_percent'] / CPU_COUNT
            if info['name'].lower() == "appserver.exe":
                protheus_services += info['cpu_percent']
                continue
            if info['cpu_percent'] < THRESHOLD:
                other_processes += info['cpu_percent']
                continue
            else:
                processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    sorted_processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)
    top_processes = sorted_processes[:TOP_PROCESSES]

    for proc in sorted_processes[TOP_PROCESSES:]:
        other_processes += proc['cpu_percent']

    if other_processes != 0:
        top_processes.append({
            'name': 'Outros Processos',
            'cpu_percent': round(other_processes, 2)
        })
    if protheus_services != 0:
        top_processes.append({
            'name': 'Protheus',
            'cpu_percent': round(protheus_services, 2)
        })
    return top_processes


async def per_process_usage():
    global all_data, last_minute
    processes = get_processes()

    now = datetime.now()
    current_minute = now.minute
    for proc in processes:
        name = proc['name']
        if name not in per_process_minute_readings:
            per_process_minute_readings[name] = {
                'name': name,
                'readings': deque(maxlen=SECONDS_IN_MINUTE)
            }
        per_process_minute_readings[name]['readings'].append(proc['cpu_percent'])

    if last_minute is None:
        last_minute = current_minute
        return None

    if current_minute != last_minute:
        minute_averages = {}
        for entry in per_process_minute_readings.values():
            if entry['readings']:
                avg = sum(entry['readings']) / len(entry['readings'])
                minute_averages[entry['name']] = round(avg, 2)

        all_data.append(minute_averages)
        per_process_minute_readings.clear()
        last_minute = current_minute
        hourly_data.append([now.strftime("%H:%M"), average(all_data)])
        return hourly_data
    return None


# ----- Service-based usage for appserver.exe -----
def get_appserver_service_pids():
    """
    Returns a dict mapping pid -> display_name for running services whose process is appserver.exe.
    """
    pid_to_display_name = {}
    for service in psutil.win_service_iter():
        try:
            svc = service.as_dict()
            if svc['status'] != 'running':
                continue
            pid = svc.get('pid')
            if not pid:
                continue
            try:
                proc = psutil.Process(pid)
                if proc.name().lower() == "appserver.exe":
                    pid_to_display_name[pid] = svc['display_name']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        except Exception:
            continue
    return pid_to_display_name


async def per_appserver_service_usage():
    """
    Collects CPU usage for all Windows services running appserver.exe.
    Returns a list of dicts with 'display_name' and 'cpu_percent'.
    Uses the same logic as per_process_usage.
    """
    global per_appserver_service_minute_readings, appserver_service_hourly_data, last_service_minute

    pid_to_display_name = get_appserver_service_pids()
    now = datetime.now()
    current_minute = now.minute

    # Gather cpu_percent for all processes
    pid_cpu = {}
    for proc in psutil.process_iter(['pid', 'cpu_percent']):
        try:
            pid = proc.info['pid']
            if pid in pid_to_display_name:
                pid_cpu[pid] = proc.info['cpu_percent'] / CPU_COUNT
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Store readings per service
    for pid, display_name in pid_to_display_name.items():
        if display_name not in per_appserver_service_minute_readings:
            per_appserver_service_minute_readings[display_name] = {
                'display_name': display_name,
                'readings': deque(maxlen=SECONDS_IN_MINUTE)
            }
        per_appserver_service_minute_readings[display_name]['readings'].append(pid_cpu.get(pid, 0.0))

    # On minute change, average and store
    if last_service_minute is None:
        last_service_minute = current_minute
        return None

    if current_minute != last_service_minute:
        minute_averages = {}
        for entry in per_appserver_service_minute_readings.values():
            if entry['readings']:
                avg = sum(entry['readings']) / len(entry['readings'])
                minute_averages[entry['display_name']] = round(avg, 2)
        appserver_service_hourly_data.append([now.strftime("%H:%M"), minute_averages])
        per_appserver_service_minute_readings.clear()
        last_service_minute = current_minute
        return appserver_service_hourly_data
    return None


# ----- Data collection and return -----
async def get_data(db):
    """Collect and store current data in memory (process and service)."""
    global last_hour, last_day, last_week

    await per_process_usage()
    await per_appserver_service_usage()

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

    # store per-process
    if current_hour != last_hour and appserver_service_hourly_data:
        data_p = [entry[1] for entry in appserver_service_hourly_data]
        if data_p and await store_per_process_hourly(db, average(data_p)):
            last_hour = current_hour
    if current_day != last_day and appserver_service_hourly_data:
        data_p = [entry[1] for entry in appserver_service_hourly_data]
        if data_p and await store_per_process_daily(db, average(data_p)):
            last_day = current_day
    if current_week != last_week and appserver_service_hourly_data:
        data_p = [entry[1] for entry in appserver_service_hourly_data]
        if data_p and await store_per_process_weekly(db, average(data_p)):
            last_week = current_week

    # similarly, you can store service-based hourly/daily/weekly if needed

def return_data():
    return hourly_data

def return_services():
    return appserver_service_hourly_data