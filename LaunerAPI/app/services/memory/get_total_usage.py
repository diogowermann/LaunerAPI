"""CPU usage monitoring service - In-memory data collection."""

import psutil
from collections import deque
import logging
from datetime import datetime
from app.services.memory.store_in_database import store_total_hourly, store_total_daily, store_total_weekly

logger = logging.getLogger(__name__)

# CONSTANTS
SECONDS_IN_MINUTE = 60
MINUTES_IN_HOUR = 60

# GLOBAL VARS
total_minute_readings = deque(maxlen=SECONDS_IN_MINUTE)
hourly_data = deque(maxlen=MINUTES_IN_HOUR)  # Last 60 minutes of data
last_minute = None
last_hour = None
last_day = None
last_week = None

async def total_usage():
    global last_minute
    memory_total = psutil.virtual_memory().percent

    now = datetime.now()
    current_minute = now.minute
    total_minute_readings.append(memory_total)

    if last_minute is None:
        last_minute = current_minute
        return None
    
    if current_minute != last_minute:
        minute_avg = sum(total_minute_readings) / len(total_minute_readings)
        minute_avg = round(minute_avg, 2)
        
        total_minute_readings.clear()
        last_minute = current_minute
        hourly_data.append(minute_avg)
        return hourly_data
    return None


async def get_data(db):
    """Collect and store current data in memory."""
    global last_hour, last_day, last_week
    
    collected = await total_usage()

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
        data = hourly_data
        if data and await store_total_hourly(db, data):
            last_hour = current_hour

    if current_day != last_day and collected:
        data = hourly_data
        if data and await store_total_daily(db):
            last_day = current_day

    if current_week != last_week and collected:
        data = hourly_data
        if data and await store_total_daily(db):
            last_week = current_week

def return_data():
    return hourly_data