from sqlalchemy import Column, Integer, String
from app.database import Base

class SysUsr(Base):
    __tablename__ = 'api_launer_usr'
    api_usr_codigo = Column(String, primary_key=True)
    api_usr_pwd = Column(String)
    api_default_pwd = Column(Integer)