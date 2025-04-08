import hashlib
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from app.models.protheus import SysUsr
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "your-secret-key"  # Replace with a secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def create_access_token(data: dict):
    """Create a JWT token with expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

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
    
    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}