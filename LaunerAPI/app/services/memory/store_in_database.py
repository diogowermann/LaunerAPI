from sqlalchemy.orm import Session
from typing import List, Dict
from app.models.memory_usage import MemoryUsageTotal, MemoryUsageProcesses, UsageType
from statistics import mean
import logging

# CONSTANTS
HOURLY_STORE_INTERVAL = 3600  # Store hourly data every 1 hour (3600 seconds)
DAILY_STORE_INTERVAL = 86400  # Store daily data every 24 hours
WEEKLY_STORE_INTERVAL = 604800  # Store weekly data every 7 days
INCREASE_THRESHOLD = 1.2
HOURS_IN_DAY = 24
DAYS_IN_WEEK = 7

# GLOBAL VARIABLES
logger = logging.getLogger(__name__)

async def calculate_average(data: List[Dict]):
    """Group processes by name and calculate averages"""
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("Invalid data format: Expected a list of dictionaries")
    
    averages = {}
    for time_slice in data:
        for process in time_slice:
            name = process['name']
            if name not in averages:
                averages[name] = []
            averages[name].append(float(process['memory_percent']))
    return averages

async def store_per_process_hourly(db: Session, data: Dict) -> bool:
    """
    Store hourly Memory usage in database.
    """
    if not data:
        logger.warning("==MEM== No data to store")
        return 
    
    filtered_data = [item for item in data if isinstance(item, dict)]
    process_averages = await calculate_average(filtered_data)

    try:
        for name, usage in process_averages.items():
            db_record = MemoryUsageProcesses(
                name=name,
                tipo=UsageType.hourly,
                uso=usage,
                pid=0
            )
            
            try:
                last_record = db.query(MemoryUsageProcesses)\
                    .filter(MemoryUsageProcesses.name == name,
                            MemoryUsageProcesses.tipo == UsageType.hourly)\
                    .order_by(MemoryUsageProcesses.timestamp.desc())\
                    .first()
                last_usage = float(last_record.uso) if last_record else None
            except Exception as e:
                logger.warning(f"==MEM== Erro ao buscar último registro de {name}: {str(e)}")
                last_usage = None
            
            db.add(db_record)
            
            if last_usage and usage > last_usage * INCREASE_THRESHOLD:
                logger.warning(
                    f"==MEM== Aumento significativo de Memory - Processo: {usage}"
                    f" Anterior: {last_usage}% Atual: {usage}%"
                )
            else:
                logger.info(f"==MEM== Média horária armazenada - Processo: {name} Uso: {usage}%")
                
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"==MEM== Erro ao armazenar médias horárias: {str(e)}")
        db.rollback()
        return False

async def store_per_process_daily(db: Session, data: Dict) -> bool:
    """
    Store daily Memory usage averages in database.
    """
    if not data:
        logger.warning("==MEM== No data to store")
        return 
    
    filtered_data = [item for item in data if isinstance(item, dict)]
    process_averages = await calculate_average(filtered_data)

    try:
        for name, usage in process_averages.items():
            try:
                # Get last 24 hourly records for this process
                hourly_records = db.query(MemoryUsageProcesses)\
                    .filter(MemoryUsageProcesses.name == name,
                            MemoryUsageProcesses.tipo == UsageType.hourly)\
                    .order_by(MemoryUsageProcesses.timestamp.desc())\
                    .limit(HOURS_IN_DAY)\
                    .all()
                
                if hourly_records:
                    daily_avg = mean([record.uso for record in hourly_records])
                    
                    db_record = MemoryUsageProcesses(
                        name=name,
                        tipo=UsageType.daily,
                        uso=daily_avg,
                        pid=0
                    )
                    
                    try:
                        last_record = db.query(MemoryUsageProcesses)\
                            .filter(MemoryUsageProcesses.name == name,
                                    MemoryUsageProcesses.tipo == UsageType.daily)\
                            .order_by(MemoryUsageProcesses.timestamp.desc())\
                            .first()
                        last_usage = float(last_record.uso) if last_record else None
                    except Exception as e:
                        logger.warning(f"==MEM== Erro ao buscar último registro de {name}: {str(e)}")
                        last_usage = None
                    
                    db.add(db_record)
                    
                    if last_usage and usage > last_usage * INCREASE_THRESHOLD:
                        logger.warning(
                            f"==MEM== Aumento significativo de CPU - Processo: {usage}"
                            f" Anterior: {last_usage}% Atual: {usage}%"
                        )
                    else:
                        logger.info(f"==MEM== Media diaria armazenada - Processo: {name} Uso: {usage}%")
                
            except Exception as e:
                logger.warning(f"==MEM== Erro ao processar media diaria de {name}: {str(e)}")
                continue
                
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"==MEM== Erro ao armazenar medias diarias: {str(e)}")
        db.rollback()
        return False

async def store_per_process_weekly(db: Session, data: Dict) -> bool:
    """
    Store weekly Memory usage averages in database.
    """
    if not data:
        logger.warning("==MEM== No data to store")
        return 
    
    filtered_data = [item for item in data if isinstance(item, dict)]
    process_averages = await calculate_average(filtered_data)

    try:
        for name, usage in process_averages.items():
            try:
                # Get last 7 daily records for this process
                daily_records = db.query(MemoryUsageProcesses)\
                    .filter(MemoryUsageProcesses.name == name,
                            MemoryUsageProcesses.tipo == UsageType.daily)\
                    .order_by(MemoryUsageProcesses.timestamp.desc())\
                    .limit(DAYS_IN_WEEK)\
                    .all()
                
                if daily_records:
                    weekly_avg = mean([record.uso for record in daily_records])
                    
                    db_record = MemoryUsageProcesses(
                        name=name,
                        tipo=UsageType.weekly,
                        uso=weekly_avg,
                        pid=0
                    )
                    try:
                        last_record = db.query(MemoryUsageProcesses)\
                            .filter(MemoryUsageProcesses.name == name,
                                    MemoryUsageProcesses.tipo == UsageType.weekly)\
                            .order_by(MemoryUsageProcesses.timestamp.desc())\
                            .first()
                        last_usage = float(last_record.uso) if last_record else None
                    except Exception as e:
                        logger.warning(f"==MEM== Erro ao buscar último registro de {name}: {str(e)}")
                        last_usage = None
                    
                    db.add(db_record)
                    
                    if last_usage and usage > last_usage * INCREASE_THRESHOLD:
                        logger.warning(
                            f"==MEM== Aumento significativo de CPU - Processo: {usage}"
                            f" Anterior: {last_usage}% Atual: {usage}%"
                        )
                    else:
                        logger.info(f"==CPU== Media semanal armazenada - Processo: {name} Uso: {usage}%")
                
            except Exception as e:
                logger.warning(f"==MEM== Erro ao processar média semanal de {name}: {str(e)}")
                continue
                
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"==MEM== Erro ao armazenar médias semanais: {str(e)}")
        db.rollback()
        return False

async def store_total_hourly(db: Session, data: List) -> bool:
    """
    Store hourly Memory total usage averages in database.
    """    
    if not data:
        logger.warning("==MEM== No data to store")
        return    
    try:
        avg_usage = round(mean(data), 2)
        db_record = MemoryUsageTotal(
            tipo=UsageType.hourly,
            uso=avg_usage
        )
        
        try:
            last_record = db.query(MemoryUsageTotal)\
                .filter(MemoryUsageTotal.tipo == UsageType.hourly)\
                .order_by(MemoryUsageTotal.timestamp.desc())\
                .first()
            last_usage = float(last_record.uso) if last_record else None
        except Exception as e:
            logger.warning(f"==MEM== Erro ao buscar último registro total: {str(e)}")
            last_usage = None
        
        db.add(db_record)
        
        if last_usage and avg_usage > last_usage * INCREASE_THRESHOLD:
            logger.warning(
                f"==MEM== Aumento significativo de Memory Total"
                f" Anterior: {last_usage}% Atual: {avg_usage}%"
            )
        else:
            logger.info(f"==MEM== Média horária total armazenada - Uso: {avg_usage}%")
            
        db.commit()
        return True
            
    except Exception as e:
        logger.error(f"==MEM== Erro ao armazenar média horária total: {str(e)}")
        db.rollback() 
        return False

async def store_total_daily(db: Session) -> bool:
    """
    Store daily Memory total usage averages in database.
    """
    try:
        # Get last 24 hourly records
        hourly_records = db.query(MemoryUsageTotal)\
            .filter(MemoryUsageTotal.tipo == UsageType.hourly)\
            .order_by(MemoryUsageTotal.timestamp.desc())\
            .limit(HOURS_IN_DAY)\
            .all()
        
        if hourly_records:
            daily_avg = mean([record.uso for record in hourly_records])
            
            db_record = MemoryUsageTotal(
                tipo=UsageType.daily,
                uso=daily_avg
            )
            
            db.add(db_record)
            logger.info(f"==MEM== Média diária total armazenada - Uso: {daily_avg}%")
            
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"==MEM== Erro ao armazenar média diária total: {str(e)}")
        db.rollback()
        return False

async def store_total_weekly(db: Session) -> bool:
    """
    Store weekly Memory total usage averages in database.
    """
    try:
        # Get last 7 daily records
        daily_records = db.query(MemoryUsageTotal)\
            .filter(MemoryUsageTotal.tipo == UsageType.daily)\
            .order_by(MemoryUsageTotal.timestamp.desc())\
            .limit(DAYS_IN_WEEK)\
            .all()
        
        if daily_records:
            weekly_avg = mean([record.uso for record in daily_records])
            
            db_record = MemoryUsageTotal(
                tipo=UsageType.weekly,
                uso=weekly_avg
            )
            
            db.add(db_record)
            logger.info(f"==MEM== Média semanal total armazenada - Uso: {weekly_avg}%")
            
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"==MEM== Erro ao armazenar média semanal total: {str(e)}")
        db.rollback()
        return False
