from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.config.logging_config import setup_logging
from app.config.settings import CORS_ORIGINS
from app.db.database import engine, Base
from app.db import models

setup_logging()   # logging sabse pehle — taaki startup ke logs bhi capture hon

app = FastAPI(title="AI Developer Assistant", version="1.0.0")

# Browser se aane wali requests (React etc.) ke liye — bina iske frontend
# ki har request browser hi block kar deta hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Conversation-Id"],   # frontend ko conversation id chahiye
)

Base.metadata.create_all(bind=engine)

app.include_router(health_router)   # sirf ek baar ✅
app.include_router(chat_router)

@app.get("/")
def home():
    return {"message": "Welcome to AI Developer Assistant"}