from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_protheus_db
from app.core.security import LoginData
from app.core.security import authenticate_user
from fastapi.middleware.cors import CORSMiddleware


def setup_routes(app):
    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    @app.get("/")
    async def get_app():
        return {"message": "FastAPI running"}

    @app.post("/login")
    async def login(login_data: LoginData, db: Session = Depends(get_protheus_db)):
        """Login user."""
        user = authenticate_user(db, login_data.username, login_data.password)
        return {"message": "Login realizado com sucesso!"}    
        