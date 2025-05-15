from app.services.cpu.get_per_process_usage import get_data as cpu_per_process
from app.services.cpu.get_total_usage import get_data as cpu_total
from app.services.memory.get_per_process_usage import get_data as mem_per_process
from app.services.memory.get_total_usage import get_data as mem_total
from app.database import get_protheus_db
import asyncio
import logging

logger = logging.getLogger(__name__)

async def collect_data():
    """Background task to collect CPU and memory usage data."""
    while True:
        db = None
        try:
            db = next(get_protheus_db())
            await cpu_total(db)
            await cpu_per_process(db)
            await mem_total(db)
            await mem_per_process(db)
        except Exception as e:
            logger.error(f"Error collecting system data: {str(e)}", exc_info=True)
        finally:
            if db:
                db.close()
            await asyncio.sleep(1)