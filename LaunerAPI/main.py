from fastapi import FastAPI
from app.routes.setup import router, setup_middleware, setup_static_files

app = FastAPI()

# Setup CORS middleware early
setup_middleware(app)

# Include API routes
app.include_router(router, prefix="/api")

# Setup static files
setup_static_files(app)