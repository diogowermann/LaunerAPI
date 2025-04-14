from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Numeric, func, Enum
import enum

class UsageType(enum.Enum):
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"

class MemoryUsageTotal(Base):
    """Table that contains the total memory usage infos."""
    __tablename__ = 'api_launer_memory_total'
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now())
    tipo = Column(Enum(UsageType, name="tipo"))
    uso = Column(Numeric(5, 2))

class MemoryUsageProcesses(Base):
    """Table that contains memory usage infos per process."""
    __tablename__ = 'api_launer_memory_proc'
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now())
    pid = Column(Integer)
    name = Column(String(255))
    tipo = Column(Enum(UsageType, name="tipo"))
    uso = Column(Numeric(5, 2))