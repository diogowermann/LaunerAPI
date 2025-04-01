from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def get_app():
    return {"message": "FastAPI running"}