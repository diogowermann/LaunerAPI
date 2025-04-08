# setup.py
from fastapi import APIRouter, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import get_protheus_db
from app.core.security import LoginData, authenticate_user
from fastapi.middleware.cors import CORSMiddleware

router = APIRouter()

@router.get("/")
async def get_app():
    return {"message": "FastAPI running"}

@router.post("/login")
async def login(login_data: LoginData, db: Session = Depends(get_protheus_db)):
    user = authenticate_user(db, login_data.username, login_data.password)    
    return user

def setup_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_static_files(app):
    app.mount("/static", StaticFiles(directory="frontend/src"), name="static")
    app.mount("/", StaticFiles(directory="frontend/src/pages", html=True), name="react")