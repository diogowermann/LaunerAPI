from fastapi import FastAPI
from app.routes.setup import setup_routes
app = FastAPI()

setup_routes(app)
