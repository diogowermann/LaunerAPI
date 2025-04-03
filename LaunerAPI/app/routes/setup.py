def setup_routes(app):
    @app.get("/")
    async def get_app():
        return {"message": "FastAPI running"}
    
        