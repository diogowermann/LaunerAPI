from fastapi import FastAPI
import asyncio
from app.services.tasks import collect_data
from app.routes.setup import router, setup_middleware, setup_static_files
from app.core.logging import setup_logging

setup_logging()  # Setup logging before starting the app

app = FastAPI()

# Setup CORS middleware early
setup_middleware(app)

# Include API routes
app.include_router(router, prefix="/api")

# Setup static files
setup_static_files(app)

@app.on_event("startup")
async def start_collector():
    asyncio.create_task(collect_data())