# ─── Application Configuration ────────────────────────────────────────────────
# Saari configuration ek jagah — agar kuch badlna ho toh sirf yahan badlo
# Values .env file se load hoti hain (see .env.example) — agar .env mein na ho,
# toh neeche wale defaults use ho jaate hain.

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Ollama (Local AI) Settings ───────────────────────────────────────────────
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")  # Ollama local server ka address
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")           # Use hone wala AI model

# Alternative models (use karna ho toh .env mein OLLAMA_MODEL set karo):
# OLLAMA_MODEL = "qwen2.5-coder:7b"   # coding ke liye behtar, par bada aur dheema
#
# qwen3 models se bacho — wo reasoning models hain. Thinking off karne ke baad
# bhi wo content mein sochte rehte hain: is machine pe "say hi in 3 words" ke
# liye qwen3:4b ne 2616 tokens aur 229 second liye, jabki llama3.2:3b ne
# 4 tokens aur 3 second.

# Ollama tak pahunchne ka timeout (seconds)
OLLAMA_CONNECT_TIMEOUT = float(os.getenv("OLLAMA_CONNECT_TIMEOUT", "10"))

# Do tokens ke beech max gap. Poore jawab ki limit nahi — lamba jawab chalta
# rahega, par Ollama chup ho jaye toh request hamesha ke liye nahi latkegi.
OLLAMA_READ_TIMEOUT = float(os.getenv("OLLAMA_READ_TIMEOUT", "60"))

# ─── Anthropic (Claude) Settings ──────────────────────────────────────────────
# Ek jawab max kitna lamba ho sakta hai. Ye cost cap hai — API par har token ke
# paise lagte hain, aur chat ke jawab itne lambe hote hi nahi.
ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192"))

# ─── Database Settings ────────────────────────────────────────────────────────
# Format: postgresql://username:password@host/database_name
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ai_user:ai_password@localhost/ai_assistant")

# ─── Logging Settings ─────────────────────────────────────────────────────────
# Kitni detail mein logs chahiye: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ─── Chat Limits ──────────────────────────────────────────────────────────────
# Ek message max kitna lamba ho sakta hai — isse bade message reject ho jaate hain
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "4000"))

# Context ke liye pichhle kitne messages LLM ko bheje jaate hain.
# Zyada rakhoge toh AI ko context zyada milega par response dheema hoga.
HISTORY_MESSAGE_LIMIT = int(os.getenv("HISTORY_MESSAGE_LIMIT", "20"))

# Sirf message count kaafi nahi hai — 20 chhote messages aur 20 bade messages
# mein zameen-aasmaan ka farak hai. Ye character budget asli guard hai
# (roughly 4 characters = 1 token, toh 16000 chars ≈ 4000 tokens).
HISTORY_CHAR_BUDGET = int(os.getenv("HISTORY_CHAR_BUDGET", "16000"))

# Sidebar ek baar mein kitni conversations maangti hai. Bina limit ke 500
# conversations hone par saari ek saath aa jaati thin.
CONVERSATION_PAGE_SIZE = int(os.getenv("CONVERSATION_PAGE_SIZE", "50"))

# ─── Rate limiting ────────────────────────────────────────────────────────────
# Chat endpoint har request par LLM chalata hai. Ye limit ek client ko poora
# backend jam karne se rokti hai. 0 karne par limit band ho jaati hai.
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW = float(os.getenv("RATE_LIMIT_WINDOW", "60"))

# ─── CORS Settings ────────────────────────────────────────────────────────────
# Kaun se frontend origins is API ko browser se call kar sakte hain.
# Comma se alag karke likho, e.g. "http://localhost:3000,http://localhost:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
    if origin.strip()
]