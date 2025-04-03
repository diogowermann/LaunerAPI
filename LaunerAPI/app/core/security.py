import hashlib
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.models.protheus import SysUsr

class LoginData(BaseModel):
    username: str
    password: str

def hash_password(password: str) -> str:
    """Hash the password using double sha256 algorithm."""
    return hashlib.sha256(hashlib.sha256(password.encode('windows-1252')).digest()).hexdigest()

def authenticate_user(db: Session, username: str, password: str):
    """Verify user credentials."""
    password = hash_password(password)
    user = db.query(SysUsr).filter(SysUsr.api_usr_codigo == username, SysUsr.api_usr_pwd == password).first()

    if not user:
        info = f"Credenciais Inválidas:\ndb: {db}, username: {username}, password: {password}"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=info,
            headers={"WWW-Authenticate": "Bearer"},            
        )
    