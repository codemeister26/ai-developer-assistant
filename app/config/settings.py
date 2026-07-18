# ─── Application Configuration ────────────────────────────────────────────────
# Saari configuration ek jagah — agar kuch badlna ho toh sirf yahan badlo

# ─── Ollama (Local AI) Settings ───────────────────────────────────────────────
OLLAMA_HOST = "http://localhost:11434"  # Ollama local server ka address
OLLAMA_MODEL = "llama3.2:3b"           # Use hone wala AI model

# Alternative models (use karna ho toh upar wali line change karo):
# OLLAMA_MODEL = "qwen3:4b"
# OLLAMA_MODEL = "qwen3:1.7b"

# ─── Database Settings ────────────────────────────────────────────────────────
# Format: postgresql://username:password@host/database_name
DATABASE_URL = "postgresql://ai_user:ai_password@localhost/ai_assistant"