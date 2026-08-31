# AI Developer Assistant

A production-grade AI Developer Assistant built from scratch — to learn and implement
Backend Engineering, LLM Integration, RAG Pipelines, and Agentic AI systems.

> Built by learning. Designed for scale.

---

## What Is This?

Most developers use ready-made AI frameworks and never understand what happens inside.
This project is different — every layer is built from scratch, with full understanding
of why each decision was made.

This is not just a project. It is a learning journey from zero to production-grade AI systems.

---

## Current Features

- FastAPI backend with clean layered architecture
- Ollama integration for local LLM support (no API cost)
- Persistent conversation memory using PostgreSQL
- Multi-conversation support with conversation IDs
- Streaming responses — token by token, just like ChatGPT
- Multiple AI prompts — code review, debugging, explanation, architecture
- Config-based model management — switch models in one place

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| AI Runtime | Ollama |
| LLM Model | Llama 3.2 3B |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |

---

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── chat.py          # Chat endpoint — receives requests
│   │   └── health.py        # Health check endpoint
│   │
│   ├── config/
│   │   ├── settings.py      # All configuration — one place
│   │   └── prompts.py       # AI system prompts
│   │
│   ├── db/
│   │   ├── database.py      # PostgreSQL connection setup
│   │   ├── models.py        # Database tables
│   │   └── chat_repository.py  # All database operations
│   │
│   ├── llm/
│   │   └── ollama_client.py # Ollama integration + streaming
│   │
│   ├── memory/
│   │   └── chat_memory.py   # Conversation history management
│   │
│   ├── schemas/
│   │   └── chat.py          # Request and response models
│   │
│   ├── services/
│   │   └── chat_service.py  # Core business logic — brain of the app
│   │
│   └── main.py              # Entry point — FastAPI app
│
├── requirements.txt
└── README.md
```

---

## Architecture

```text
Client (Postman / Browser / React)
              ↓
        Router Layer
       (api/chat.py)
              ↓
       Service Layer
    (chat_service.py)
       ↓           ↓
  Memory Layer   LLM Layer
(chat_memory.py) (ollama_client.py)
       ↓           ↓
  PostgreSQL     Ollama
  (Database)   (llama3.2:3b)
```

Each layer has one job. Change one layer — nothing else breaks.

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/ai-developer-assistant.git
cd ai-developer-assistant/backend
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup PostgreSQL

```bash
brew install postgresql@16
brew services start postgresql@16

psql postgres
```

```sql
CREATE DATABASE ai_assistant;
CREATE USER ai_user WITH PASSWORD 'ai_password';
GRANT ALL PRIVILEGES ON DATABASE ai_assistant TO ai_user;
GRANT ALL ON SCHEMA public TO ai_user;
\q
```

### 5. Start Ollama

```bash
ollama serve
ollama run llama3.2:3b
```

### 6. Start the server

```bash
python3 -m uvicorn app.main:app --reload
```

### 7. Open API docs

```
http://127.0.0.1:8000/docs
```