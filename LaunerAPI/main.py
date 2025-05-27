from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import asyncio
import os
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
## For Production
##    @app.get("/{full_path:path}")
##    async def catch_all(request: Request):
##        return FileResponse("frontend/build/index.html")

@app.on_event("startup")
async def start_collector():
    asyncio.create_task(collect_data())