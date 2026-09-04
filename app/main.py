from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.config.logging_config import setup_logging
from app.db.database import engine, Base
from app.db import models

setup_logging()   # logging sabse pehle — taaki startup ke logs bhi capture hon

app = FastAPI(title="AI Developer Assistant", version="1.0.0")

Base.metadata.create_all(bind=engine)

app.include_router(health_router)   # sirf ek baar ✅
app.include_router(chat_router)

@app.get("/")
def home():
    return {"message": "Welcome to AI Developer Assistant"}