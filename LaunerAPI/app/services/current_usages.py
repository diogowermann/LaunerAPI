"""
Returns current usages for the frontend when requested.
"""

"""Imports"""
import psutil
from collections import deque
from sqlalchemy.orm import Session
from app.models.cpu_usage import CPUUsageTotal
from app.models.memory_usage import MemoryUsageTotal
import logging

"""Constants"""
CPU_THRESHOLD = 1.5
TOP_PROCESSES = 7

"Global Variables"
logger = logging.getLogger(__name__)

def cpu_usage(db: Session) -> dict:
    """Return current usages for CPU."""
    def total_usage():
        total_cpu_usage = psutil.cpu_percent(interval=1, percpu=False)
        return total_cpu_usage
    def per_process_usage():
        cpu_count = psutil.cpu_count(logical=True)
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

        top_processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)[:TOP_PROCESSES]
        top_processes.append({"name": "Outros Processos", "cpu_percent": other_processes_cpu})

        return top_processes

    def last_hourly_avg(db: Session):
        last_hourly = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == "hourly").order_by(CPUUsageTotal.timestamp.desc()).first()
        return last_hourly
    def last_daily_avg(db: Session):
        last_daily = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == "daily").order_by(CPUUsageTotal.timestamp.desc()).first()
        return last_daily
    def last_weekly_avg(db: Session):
        last_weekly = db.query(CPUUsageTotal).filter(CPUUsageTotal.tipo == "weekly").order_by(CPUUsageTotal.timestamp.desc()).first()
        return last_weekly

    total_usage_ = total_usage()
    per_process_usage_ = per_process_usage()
    last_hourly_avg_ = last_hourly_avg(db)
    last_daily_avg_ = last_daily_avg(db)
    last_weekly_avg_ = last_weekly_avg(db)

    result = {
        "total_usage": total_usage_,
        "top_processes": per_process_usage_,
        "last_hourly_avg": last_hourly_avg_,
        "last_daily_avg": last_daily_avg_,
        "last_weekly_avg": last_weekly_avg_
        }
    
    try:
        return result
    except Exception as e:
        logger.error(f"==CPU== Erro ao retornar os dados em tempo real: {str(e)}")
        logger.debug(f"==CPU== Dados: {result}")
        raise

def mem_usage(db: Session):
    """Return current usages for Memory."""
    def total_usage():
        total_memory_usage = psutil.virtual_memory().percent
        return total_memory_usage
    def per_process_usage():
        processes = []
        other_processes_memory = 0

        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        sorted_processes = sorted(processes, key=lambda p: p['memory_percent'], reverse=True)
        top_processes = sorted_processes[:TOP_PROCESSES]

        for proc in sorted_processes[TOP_PROCESSES:]:
            other_processes_memory += proc['memory_percent']

        top_processes.append({"name": "Outros Processos", "memory_percent": other_processes_memory})

        return top_processes

    def last_hourly_avg(db: Session):
        last_hourly = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == "hourly").order_by(MemoryUsageTotal.timestamp.desc()).first()
        return last_hourly
    def last_daily_avg(db: Session):
        last_daily = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == "daily").order_by(MemoryUsageTotal.timestamp.desc()).first()
        return last_daily
    def last_weekly_avg(db: Session):
        last_weekly = db.query(MemoryUsageTotal).filter(MemoryUsageTotal.tipo == "weekly").order_by(MemoryUsageTotal.timestamp.desc()).first()
        return last_weekly
    
    total_usage_ = total_usage()
    per_process_usage_ = per_process_usage()
    last_hourly_avg_ = last_hourly_avg(db)
    last_daily_avg_ = last_daily_avg(db)
    last_weekly_avg_ = last_weekly_avg(db)

    result = {
        "total_usage": total_usage_,
        "top_processes": per_process_usage_,
        "last_hourly_avg": last_hourly_avg_,
        "last_daily_avg": last_daily_avg_,
        "last_weekly_avg": last_weekly_avg_
        }
    
    try:
        return result
    except Exception as e:
        logger.error(f"==CPU== Erro ao retornar os dados em tempo real: {str(e)}")
        logger.debug(f"==CPU== Dados: {result}")
        raise

def return_all(db):
    """Functions that returns current data."""
    cpu = cpu_usage(db)
    mem = mem_usage(db)
    return {
        "cpu_values": cpu,
        "mem_values": mem
    }