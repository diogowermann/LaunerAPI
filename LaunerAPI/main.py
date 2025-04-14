from fastapi import FastAPI
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