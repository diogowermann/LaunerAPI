"""
Memory usage monitoring service.
Tracks and stores Memory usage statistics including hourly, daily, and weekly averages,
as well as per-process utilization.
"""

import psutil
from collections import deque
from sqlalchemy.orm import Session
from app.models.memory_usage import MemoryUsageTotal, MemoryUsageProcesses, UsageType
import logging
from time import time

logger = logging.getLogger(__name__)

# Constants
CACHE_DURATION = 1 # Seconds
SECONDS_IN_HOUR = 60 * 60 # Seconds in an hour
HOURS_IN_DAY = 24 # 24 hours
DAYS_IN_WEEK = 7 # 7 days
MEMORY_THRESHOLD = 1.5 # Memory usage threshold for processes to be considered "top"
MEMORY_INCREASE_THRESHOLD = 1.2 # 20% increase threshold for logging

# Set up cache for returned data to avoid frequent database queries
# and to improve performance.
class CachedData:
    """Class to cache Memory usage data"""
    def __init__(self):
        self.last_update = 0
        self.cached_value = None
memory_cache = CachedData()

# This is for mantaining the last 60 minutes of CPU usage data
# and the last 60 minutes of top processes in memory to not overload the 
# database with too many records.
hourly_memory_usage = deque(maxlen=(60*60))  # Store the last 60 minutes of total memory usage
hourly_processes = deque(maxlen=(60*60))  # Store the last 60 minutes of top processes

def calculate_average(data):
    """Helper function to calculate the average of the deque for hourly data."""
    return sum(data) / len(data) if data else 0

def store_memory_usage_data(db: Session):
    """Store hourly, daily, and weekly memory usage averages in the database."""

    last_hourly = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == "hourly").order_by(MemoryUsageTotal.timestamp.desc()).first()

    if len(hourly_memory_usage) == SECONDS_IN_HOUR:
        hourly_avg = calculate_average(hourly_memory_usage)

        hourly_total = MemoryUsageTotal(UsageType.hourly, uso=hourly_avg)
        db.add(hourly_total)

        for process in hourly_processes[-1]:  # Use the last set of top processes
            hourly_process = MemoryUsageProcesses(
                pid=process['pid'],
                name=process['name'],
                tipo="hourly",
                uso=process['memory_percent']
            )
            db.add(hourly_process)

        try:
            if last_hourly * MEMORY_INCREASE_THRESHOLD < hourly_avg:
                logger.warning(f"==MEM== Aumento de 20% no uso da memoria: {last_hourly} -> {hourly_avg}")

            db.commit()
            logger.info(f"==MEM== Media horaria armazenada com sucesso: {hourly_avg}")
        except Exception as e:
            logger.error(f"==MEM== Erro ao armazenar media horaria: {str(e)}")
            logger.debug(f"==MEM== Dados: {hourly_avg}")
            raise

        hourly_memory_usage.clear()
        hourly_processes.clear()

    calculate_daily_average(db)
    calculate_weekly_average(db)

def get_memory_usage(db: Session):
    """Get the total memory usage and the top 10 processes consuming memory."""
    current_time = time()

    if memory_cache.cached_value and (current_time - memory_cache.last_update) < CACHE_DURATION:
        return memory_cache.cached_value

    total_memory_usage = psutil.virtual_memory().percent

    hourly_memory_usage.append(total_memory_usage)

    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_processes = sorted(processes, key=lambda p: p['memory_percent'], reverse=True)[:10]
    hourly_processes.append(top_processes)

    last_hourly = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == "hourly").order_by(MemoryUsageTotal.timestamp.desc()).first()
    last_daily = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == "daily").order_by(MemoryUsageTotal.timestamp.desc()).first()
    last_weekly = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == "weekly").order_by(MemoryUsageTotal.timestamp.desc()).first()

    result = {
        "total_memory_usage": total_memory_usage,
        "top_processes": top_processes,
        "last_hourly": last_hourly.uso if last_hourly else None,
        "last_daily": last_daily.uso if last_daily else None,
        "last_weekly": last_weekly.uso if last_weekly else None,
    }

    memory_cache.cached_value = result
    memory_cache.last_update = current_time

    try:
        return result
    except Exception as e:
        logger.error(f"==MEM== Erro ao retornar os dados da funcao: {str(e)}")
        logger.debug(f"==MEM== Dados: {result}")
        raise

def calculate_daily_average(db: Session):
    """Calculate and store daily average if 24 hourly records are available"""

    last_daily = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == "daily").order_by(MemoryUsageTotal.timestamp.desc()).first()

    last_24_hours = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == UsageType.hourly).order_by(MemoryUsageTotal.timestamp.desc()).limit(24).all()
    if len(last_24_hours) == 24:
        try:
            daily_avg = sum(record.uso for record in last_24_hours) / len(last_24_hours)
            daily_total = MemoryUsageTotal(UsageType.daily, uso=daily_avg)
            db.add(daily_total)

            if last_daily * MEMORY_INCREASE_THRESHOLD <= daily_avg:
                logger.warning(f"==MEM== Aumento de 20% no uso diario da memoria: {last_daily} -> {daily_avg}")

            db.commit()
            logger.info(f"==MEM== Media diaria armazenada com sucesso: {daily_avg}")
        except Exception as e:
            logger.error(f"==MEM== Erro ao armazenar media diária: {str(e)}")
            logger.debug(f"==MEM== Dados: {daily_avg}")
            raise

def calculate_weekly_average(db: Session):
    """Calculate and store weekly average if 7 daily records are available"""

    last_weekly = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == "weekly").order_by(MemoryUsageTotal.timestamp.desc()).first()

    last_7_days = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == UsageType.daily).order_by(MemoryUsageTotal.timestamp.desc()).limit(7).all()
    if len(last_7_days) == 7:
        try:
            weekly_avg = sum(record.uso for record in last_7_days) / len(last_7_days)
            weekly_total = MemoryUsageTotal(UsageType.weekly, uso=weekly_avg)
            db.add(weekly_total)

            if last_weekly * MEMORY_INCREASE_THRESHOLD <= weekly_avg:
                logger.warning(f"==MEM== Aumento de 20% no uso semanal da memoria: {last_weekly} -> {weekly_avg}")

            db.commit()
            logger.info(f"==MEM== Media semanal armazenada com sucesso: {weekly_avg}")
        except Exception as e:
            logger.error(f"==MEM== Erro ao armazenar media semanal: {e}")
            logger.debug(f"==MEM== Dados {weekly_avg}")
            raise