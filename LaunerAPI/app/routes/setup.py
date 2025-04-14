"""
Starts the routes and middleware for the aplication.
Used for interacting with the frontend.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import get_protheus_db
from app.core.security import LoginData, authenticate_user, get_current_user
from fastapi.middleware.cors import CORSMiddleware
from app.services.cpu_usage import get_cpu_usage as real_time_cpu_usage
from app.services.memory_usage import get_memory_usage as real_time_memory_usage
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def get_app():
    """Returns only a message, for debugging purposes."""
    return {"message": "FastAPI running"}

@router.post("/login")
async def login(login_data: LoginData, db: Session = Depends(get_protheus_db)):
    """Authenticates user and logs if an user has logged succesfully or not."""
    try:
        user = authenticate_user(db, login_data.username, login_data.password)    
        logger.info(f"==LOGIN== {login_data.username} fez login com sucesso.")
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail="Credenciais Inválidas")

# Example protected route, use as template for future routes
@router.get("/protected-route")
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}!"}

@router.get("/cpu-usage")
async def get_cpu_usage(db: Session = Depends(get_protheus_db)):
    """Collects CPU usage. Return usage values in real time and store hourly, daily and 
    weekly values in the database."""
    return real_time_cpu_usage(db)

@router.get("/memory-usage")
async def get_memory_usage(db: Session = Depends(get_protheus_db)):
    """Collects Memory usage. Return usage values in real time and store hourly, daily and 
    weekly values in the database."""
    return real_time_memory_usage(db)

def setup_middleware(app):
    """Sets up middleware exceptions."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_static_files(app):
    """Sets static files for the application."""
    app.mount("/static", StaticFiles(directory="frontend/src"), name="static")
    app.mount("/", StaticFiles(directory="frontend/src/pages", html=True), name="react")