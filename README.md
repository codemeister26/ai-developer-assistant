# AI Developer Assistant

AI Developer Assistant is a backend-first project built to learn and implement Agentic AI concepts from scratch.

## Features

* FastAPI Backend
* Ollama Integration
* Local LLM Support
* Chat API
* Conversation Memory
* Modular Architecture
* Config-Based Model Management

## Tech Stack

* Python
* FastAPI
* Ollama
* Llama 3.2
* Pydantic

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   ├── config/
│   ├── llm/
│   ├── memory/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── requirements.txt
└── README.md
```

## Current Architecture

```text
Client
  ↓
Router
  ↓
Service Layer
  ↓
Memory Layer
  ↓
LLM Layer
  ↓
Ollama
```

## Getting Started

### Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start Ollama

```bash
ollama serve
```

### Run Model

```bash
ollama run llama3.2:3b
```

### Start FastAPI

```bash
python3 -m uvicorn app.main:app --reload
```

## Roadmap

* [x] FastAPI Setup
* [x] Ollama Integration
* [x] Conversation Memory
* [ ] Redis Memory
* [ ] PostgreSQL Storage
* [ ] RAG Pipeline
* [ ] File Upload Support
* [ ] OpenAI Integration
* [ ] Claude Integration
* [ ] Agentic Workflows

## Purpose

This project is being built as a hands-on journey to learn Backend Development, LLM Integration, RAG, and Agentic AI systems from beginner to advanced level.
