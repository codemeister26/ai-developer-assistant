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
- React chat UI with streaming, conversation history and a stop button

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| Frontend | React, Vite |
| AI Runtime | Ollama |
| LLM Model | Llama 3.2 3B |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Migrations | Alembic |
| Tests | pytest |

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
│   │   ├── logging_config.py  # Logging setup
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
├── alembic/                 # Database migrations
│   └── versions/
│
├── tests/                   # pytest suite
│
├── frontend/                # React chat UI (apna README hai)
│   └── src/
│
├── requirements.txt
├── requirements-dev.txt
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

### 5. Create the database tables

Schema Alembic manage karta hai — tables apne aap nahi banti:

```bash
alembic upgrade head
```

> **Pehle se database hai jisme tables maujood hain?**
> Migration dobara mat chalao. Bas bata do ki wo already up to date hai:
>
> ```bash
> alembic stamp head
> ```

### 6. Start Ollama

```bash
ollama serve
ollama run llama3.2:3b
```

### 7. Start the server

```bash
python3 -m uvicorn app.main:app --reload
```

### 8. Open API docs

```
http://127.0.0.1:8000/docs
```

### 9. Start the frontend (alag terminal mein)

```bash
cd frontend
npm install
npm run dev
```

Chat UI khulegi `http://localhost:5173` pe. Details: [frontend/README.md](frontend/README.md)

---

## Development

### Run tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests in-memory SQLite use karte hain — tumhare asli Postgres data ko haath nahi lagta.

### Database migrations

Jab bhi `app/db/models.py` badlo, migration banao:

```bash
alembic revision --autogenerate -m "kya badla"   # migration generate karo
alembic upgrade head                             # apply karo
alembic current                                  # abhi kis revision pe ho
alembic check                                    # models aur DB match karte hain?
alembic downgrade -1                             # pichhli migration undo karo
```

> Generated migration ko hamesha padh lo apply karne se pehle — autogenerate
> sab kuch sahi detect nahi karta.

### Push changes to GitHub

```bash
./push.sh "your commit message"
```

Stages all changes, commits with the given message, and pushes to the current branch.