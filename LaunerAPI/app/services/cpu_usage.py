"""
CPU usage monitoring service.
Tracks and stores CPU usage statistics including hourly, daily, and weekly averages,
as well as per-process utilization.
"""

import psutil
from collections import deque
from sqlalchemy.orm import Session
from app.models.cpu_usage import CPUUsageTotal, CPUUsageProcesses, UsageType
import logging
from time import time

logger = logging.getLogger(__name__)

# Constants
CACHE_DURATION = 1 # Seconds
SECONDS_IN_HOUR = 60 * 60 # Number of seconds in an hour
HOURS_IN_DAY = 24 # 24 hours
DAYS_IN_WEEK = 7 # 7 days
CPU_THRESHOLD = 1.5 # CPU usage threshold for processes to be considered "top"
CPU_INCREASE_THRESHOLD = 1.2 # 20% increase threshold for logging

# Set up cache for returned data to avoid frequent database queries
# and to improve performance.
class CachedData:
    """Class to cache CPU usage data."""
    def __init__(self):
        self.last_update = 0
        self.cached_value = None
cpu_cache = CachedData()

# This is for mantaining the last 60 minutes of CPU usage data
# and the last 60 minutes of top processes in memory to not overload the 
# database with too many records.
hourly_cpu_usage = deque(maxlen=SECONDS_IN_HOUR)
hourly_processes = deque(maxlen=SECONDS_IN_HOUR)

def calculate_average(data):
    """Helper function to calculate the average of the deque for hourly data."""
    return sum(data) / len(data) if data else 0

def store_cpu_usage_data(db: Session):
    """Store hourly, daily, and weekly CPU usage averages in the database."""

    last_hourly = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == "hourly").order_by(CPUUsageTotal.timestamp.desc()).first()

    if len(hourly_cpu_usage) == SECONDS_IN_HOUR:
        hourly_avg = calculate_average(hourly_cpu_usage)

        hourly_total = CPUUsageTotal(tipo=UsageType.hourly, uso=hourly_avg)
        db.add(hourly_total)

        for process in hourly_processes[-1]:  # Use the last set of top processes
            hourly_process = CPUUsageProcesses(
                pid=process['pid'],
                name=process['name'],
                tipo="hourly",
                uso=process['cpu_percent']
            )
            db.add(hourly_process)

        try:
            if last_hourly * CPU_INCREASE_THRESHOLD < hourly_avg:
                logger.warning(f"==CPU== Aumento de 20% no uso do CPU: {hourly_avg}")
                
            db.commit()
            logger.info(f"==CPU== Media horaria armazenada com sucesso: {hourly_avg}")
        except Exception as e:
            logger.error(f"==CPU== Erro ao armazenar media horaria: {str(e)}")
            logger.debug(f"==CPU== Dados: {hourly_avg}")
            raise

        hourly_cpu_usage.clear()
        hourly_processes.clear()

    calculate_daily_average(db)
    calculate_weekly_average(db)

def get_cpu_usage(db: Session):
    """Get the total CPU usage and the top 10 processes consuming CPU."""
    current_time = time()

    if cpu_cache.cached_value and (current_time - cpu_cache.last_update) < CACHE_DURATION:
        return cpu_cache.cached_value

    total_cpu_usage = psutil.cpu_percent(interval=1, percpu=False)
    cpu_count = psutil.cpu_count(logical=True)

    hourly_cpu_usage.append(total_cpu_usage)

    processes = []
    other_processes_cpu = 0

    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            proc_info = proc.info

            if proc_info['pid'] == 0 or proc_info['name'].lower() == "system idle process":
                continue
            proc_info['cpu_percent'] = proc_info['cpu_percent'] / cpu_count

            if proc_info['cpu_percent'] < CPU_THRESHOLD:
                other_processes_cpu += proc_info['cpu_percent']
            else:
                processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)[:10]
    top_processes.append({"name": "Other Processes", "cpu_percent": other_processes_cpu})
    hourly_processes.append(top_processes)

    last_hourly = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == "hourly").order_by(CPUUsageTotal.timestamp.desc()).first()
    last_daily = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == "daily").order_by(CPUUsageTotal.timestamp.desc()).first()
    last_weekly = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == "weekly").order_by(CPUUsageTotal.timestamp.desc()).first()

    result = {
        "total_cpu_usage": total_cpu_usage,
        "top_processes": top_processes,
        "last_hourly": last_hourly.uso if last_hourly else None,
        "last_daily": last_daily.uso if last_daily else None,
        "last_weekly": last_weekly.uso if last_weekly else None,
    }

    cpu_cache.cached_value = result
    cpu_cache.last_update = current_time

    try:
        return result
    except Exception as e:
        logger.error(f"==CPU== Erro ao retornar os dados da funcao: {str(e)}")
        logger.debug(f"==CPU== Dados: {result}")
        raise

def calculate_daily_average(db: Session):
    """Calculate and store daily average if 24 hourly records are available"""

    last_daily = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == "daily").order_by(CPUUsageTotal.timestamp.desc()).first()
    
    last_24_hours = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == UsageType.hourly).order_by(CPUUsageTotal.timestamp.desc()).limit(24).all()
    if len(last_24_hours) == 24:
        try:
            daily_avg = sum(record.usage for record in last_24_hours) / len(last_24_hours)
            daily_total = CPUUsageTotal(tipo=UsageType.daily, uso=daily_avg)
            db.add(daily_total)
            
            if last_daily * CPU_INCREASE_THRESHOLD <= daily_avg:
                logger.warning(f"==CPU== Aumento de 20% no uso diario do CPU: {daily_avg}")

            db.commit()
            logger.info(f"==CPU== Media diaria armazenada com sucesso: {daily_avg}")
        except Exception as e:
            logger.error(f"==CPU== Erro ao armazenar media diária: {str(e)}")
            logger.debug(f"==CPU== Dados: {daily_avg}")
            raise
        
def calculate_weekly_average(db: Session):
    """Calculate and store weekly average if 7 daily records are available"""

    last_weekly = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == "weekly").order_by(CPUUsageTotal.timestamp.desc()).first()
    
    last_7_days = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == UsageType.daily).order_by(CPUUsageTotal.timestamp.desc()).limit(7).all()
    if len(last_7_days) == 7:
        try:
            weekly_avg = sum(record.usage for record in last_7_days) / len(last_7_days)
            weekly_total = CPUUsageTotal(tipo=UsageType.weekly, uso=weekly_avg)
            db.add(weekly_total)
            
            if last_weekly * CPU_INCREASE_THRESHOLD <= weekly_avg:
                logger.warning(f"==CPU== Aumento de 20% no uso semanal do CPU: {weekly_avg}")

            db.commit()
            logger.info(f"==CPU== Media semanal armazenada com sucesso: {weekly_avg}")
        except Exception as e:
            logger.error(f"==CPU== Erro ao armazenar media semanal: {str(e)}")
            logger.debug(f"==CPU== Dados: {weekly_avg}")
            raise