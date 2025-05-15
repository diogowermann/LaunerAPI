from sqlalchemy.orm import Session
from typing import List, Dict
from app.models.cpu_usage import CPUUsageTotal, CPUUsageProcesses, UsageType
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
            averages[name].append(float(process['cpu_percent']))
    return averages

async def store_per_process_hourly(db: Session, data: Dict) -> bool:
    """
    Store hourly CPU usage in database.
    """
    if not data:
        logger.warning("==MEM== No data to store")
        return 
    
    filtered_data = [item for item in data if isinstance(item, dict)]
    process_averages = await calculate_average(filtered_data)

    try:
        for name, usage in process_averages.items():
            db_record = CPUUsageProcesses(
                name=name,
                tipo=UsageType.hourly,
                uso=usage,
                pid=0
            )
            
            try:
                last_record = db.query(CPUUsageProcesses)\
                    .filter(CPUUsageProcesses.name == name,
                            CPUUsageProcesses.tipo == UsageType.hourly)\
                    .order_by(CPUUsageProcesses.timestamp.desc())\
                    .first()
                last_usage = float(last_record.uso) if last_record else None
            except Exception as e:
                logger.warning(f"==CPU== Erro ao buscar último registro de {name}: {str(e)}")
                last_usage = None
            
            db.add(db_record)
            
            if last_usage and usage > last_usage * INCREASE_THRESHOLD:
                logger.warning(
                    f"==CPU== Aumento significativo de CPU - Processo: {usage}"
                    f" Anterior: {last_usage}% Atual: {usage}%"
                )
            else:
                logger.info(f"==CPU== Média horária armazenada - Processo: {name} Uso: {usage}%")
                
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"==CPU== Erro ao armazenar médias horárias: {str(e)}")
        db.rollback()
        return False
                
async def store_per_process_daily(db: Session, data: dict) -> bool:
    """
    Store daily CPU usage averages in database.
    """
    if not data:
        logger.warning("==MEM== No data to store")
        return 
    
    filtered_data = [item for item in data if isinstance(item, dict)]
    process_averages = await calculate_average(filtered_data)

    try:
        for name, usage in process_averages.items():
            try:
                # Get last 24 records for each process
                hourly_records = db.query(CPUUsageProcesses)\
                    .filter(CPUUsageProcesses.name == name,
                            CPUUsageProcesses.tipo == UsageType.hourly)\
                    .order_by(CPUUsageProcesses.timestamp.desc())\
                    .limit(HOURS_IN_DAY)\
                    .all()
                
                if hourly_records:
                    daily_avg = mean([record.uso for record in hourly_records])
                    process_averages[name] = daily_avg

            except Exception as e:
                logger.warning(f"==CPU== Error processing daily average for {name}: {str(e)}")
                continue
        for name, _ in process_averages.items():
            try:

                # Get last 24 hourly records for this process
                hourly_records = db.query(CPUUsageProcesses)\
                    .filter(CPUUsageProcesses.name == name,
                            CPUUsageProcesses.tipo == UsageType.hourly)\
                    .order_by(CPUUsageProcesses.timestamp.desc())\
                    .limit(HOURS_IN_DAY)\
                    .all()
                
                if hourly_records:
                    daily_avg = mean([record.uso for record in hourly_records])
                    
                    db_record = CPUUsageProcesses(
                        name=name,
                        tipo=UsageType.daily,
                        uso=daily_avg,
                        pid=0
                    )
                    
                    try:
                        last_record = db.query(CPUUsageProcesses)\
                            .filter(CPUUsageProcesses.name == name,
                                    CPUUsageProcesses.tipo == UsageType.daily)\
                            .order_by(CPUUsageProcesses.timestamp.desc())\
                            .first()
                        last_usage = float(last_record.uso) if last_record else None
                    except Exception as e:
                        logger.warning(f"==CPU== Erro ao buscar último registro de {name}: {str(e)}")
                        last_usage = None
                    
                    db.add(db_record)
                    
                    if last_usage and usage > last_usage * INCREASE_THRESHOLD:
                        logger.warning(
                            f"==CPU== Aumento significativo de CPU - Processo: {usage}"
                            f" Anterior: {last_usage}% Atual: {usage}%"
                        )
                    else:
                        logger.info(f"==CPU== Media diaria armazenada - Processo: {name} Uso: {usage}%")
                
            except Exception as e:
                logger.warning(f"==CPU== Erro ao processar média diária de {name}: {str(e)}")
                continue
            logger.info(f"==CPU== Media diária armazenada - Processo: {name} Uso: {daily_avg}%")
                
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"==CPU== Erro ao armazenar médias diárias: {str(e)}")
        db.rollback()
        return False

async def store_per_process_weekly(db: Session, data: Dict) -> bool:
    """
    Store weekly CPU usage averages in database.
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
                weekly_records = db.query(CPUUsageProcesses)\
                    .filter(CPUUsageProcesses.name == name,
                            CPUUsageProcesses.tipo == UsageType.weekly)\
                    .order_by(CPUUsageProcesses.timestamp.desc())\
                    .limit(DAYS_IN_WEEK)\
                    .all()
                
                if weekly_records:
                    weekly_avg = mean([record.uso for record in weekly_records])
                    
                    db_record = CPUUsageProcesses(
                        name=name,
                        tipo=UsageType.weekly,
                        uso=weekly_avg,
                        pid=0
                    )
                    try:
                        last_record = db.query(CPUUsageProcesses)\
                            .filter(CPUUsageProcesses.name == name,
                                    CPUUsageProcesses.tipo == UsageType.weekly)\
                            .order_by(CPUUsageProcesses.timestamp.desc())\
                            .first()
                        last_usage = float(last_record.uso) if last_record else None
                    except Exception as e:
                        logger.warning(f"==CPU== Erro ao buscar último registro de {name}: {str(e)}")
                        last_usage = None
                    
                    db.add(db_record)
                    
                    if last_usage and usage > last_usage * INCREASE_THRESHOLD:
                        logger.warning(
                            f"==CPU== Aumento significativo de CPU - Processo: {usage}"
                            f" Anterior: {last_usage}% Atual: {usage}%"
                        )
                    else:
                        logger.info(f"==CPU== Media semanal armazenada - Processo: {name} Uso: {usage}%")
                
            except Exception as e:
                logger.warning(f"==CPU== Erro ao processar media semanal de {name}: {str(e)}")
                continue
                
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"==CPU== Erro ao armazenar medias semanais: {str(e)}")
        db.rollback()
        return False

async def store_total_hourly(db: Session, data: List) -> bool:
    """
    Store hourly CPU total usage averages in database.
    """        
    try:
        avg_usage = mean(data)
        db_record = CPUUsageTotal(
            tipo=UsageType.hourly,
            uso=avg_usage
        )
        
        try:
            last_record = db.query(CPUUsageTotal)\
                .filter(CPUUsageTotal.tipo == UsageType.hourly)\
                .order_by(CPUUsageTotal.timestamp.desc())\
                .first()
            last_usage = float(last_record.uso) if last_record else None
        except Exception as e:
            logger.warning(f"==CPU== Erro ao buscar último registro total: {str(e)}")
            last_usage = None
        
        db.add(db_record)
        
        if last_usage and avg_usage > last_usage * INCREASE_THRESHOLD:
            logger.warning(
                f"==CPU== Aumento significativo de CPU Total"
                f" Anterior: {last_usage}% Atual: {avg_usage}%"
            )
        else:
            logger.info(f"==CPU== Media horaria total armazenada - Uso: {avg_usage}%")
            
        db.commit()
        return True
            
    except Exception as e:
        logger.error(f"==CPU== Erro ao armazenar media horaria total: {str(e)}")
        db.rollback() 
        return False

async def store_total_daily(db: Session) -> bool:
    """
    Store daily CPU total usage averages in database.
    """
    try:
        # Get last 24 hourly records
        hourly_records = db.query(CPUUsageTotal)\
            .filter(CPUUsageTotal.tipo == UsageType.hourly)\
            .order_by(CPUUsageTotal.timestamp.desc())\
            .limit(HOURS_IN_DAY)\
            .all()
        
        if hourly_records:
            daily_avg = mean([record.uso for record in hourly_records])
            
            db_record = CPUUsageTotal(
                tipo=UsageType.daily,
                uso=daily_avg
            )
            
            db.add(db_record)
            logger.info(f"==CPU== Media diaria total armazenada - Uso: {daily_avg}%")
            
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"==CPU== Erro ao armazenar media diaria total: {str(e)}")
        db.rollback()
        return False

async def store_total_weekly(db: Session) -> bool:
    """
    Store weekly CPU total usage averages in database.
    """
    try:
        # Get last 7 daily records
        daily_records = db.query(CPUUsageTotal)\
            .filter(CPUUsageTotal.tipo == UsageType.daily)\
            .order_by(CPUUsageTotal.timestamp.desc())\
            .limit(DAYS_IN_WEEK)\
            .all()
        
        if daily_records:
            weekly_avg = mean([record.uso for record in daily_records])
            
            db_record = CPUUsageTotal(
                tipo=UsageType.weekly,
                uso=weekly_avg
            )
            
            db.add(db_record)
            logger.info(f"==CPU== Media semanal total armazenada - Uso: {weekly_avg}%")
            
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"==CPU== Erro ao armazenar media semanal total: {str(e)}")
        db.rollback()
        return False
