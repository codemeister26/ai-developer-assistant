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
# OLLAMA_MODEL = "qwen3:4b"
# OLLAMA_MODEL = "qwen3:1.7b"

# ─── Database Settings ────────────────────────────────────────────────────────
# Format: postgresql://username:password@host/database_name
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ai_user:ai_password@localhost/ai_assistant")