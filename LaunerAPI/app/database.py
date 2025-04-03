from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

PROTHEUS_DB_URL = "postgresql+psycopg2://postgres:@192.168.0.204:5432/producao" 

engine = create_engine(PROTHEUS_DB_URL, pool_pre_ping=True, connect_args={"options": "-c timezone=utc-3"})

ProtheusSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_protheus_db():
    db = ProtheusSessionLocal()
    try:
        yield db
    finally:
        db.close()