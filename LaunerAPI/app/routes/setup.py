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
from app.services.current_usages import return_all
from app.services.merge_total_data import return_data as total_data
from app.services.cpu.get_per_process_usage import return_data as last_minutes_cpu_per_process_data, return_services as cpu_services_data
from app.services.memory.get_per_process_usage import return_data as last_minutes_mem_per_process_data, return_services as mem_services_data
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

@router.get("/current-usages")
def get_current_usages(db: Session = Depends(get_protheus_db)):
    """Collects current usage values."""
    return return_all(db)

@router.get("/last-60-minutes")
def get_last():
    """Returns last 60 minutes of data for CPU and Memory"""
    total = total_data()
    per_process_cpu = last_minutes_cpu_per_process_data()
    per_process_mem = last_minutes_mem_per_process_data()    
    
    return {"total_data": total, "cpu_data": per_process_cpu, "memory_data": per_process_mem}

@router.get("/last-60-minutes-services")
def get_last():
    cpu = cpu_services_data()
    memory = mem_services_data()
    return {"cpu": cpu, "memory": memory}

def setup_middleware(app):
    """Sets up middleware exceptions."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_static_files(app):
    """Sets static files for the application."""
    app.mount("/static", StaticFiles(directory="frontend/src"), name="static")
    app.mount("/", StaticFiles(directory="frontend/src/pages", html=True), name="react")