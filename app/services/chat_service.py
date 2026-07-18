from app.llm.ollama_client import generate_response_stream
from app.memory.chat_memory import get_history, add_message
from typing import Generator

def get_ai_response_stream(message: str) -> Generator[str, None, None]:
    user_id = "default_user"

    add_message(user_id=user_id, role="user", content=message)

    history = get_history(user_id)
    full_response = ""

    for chunk in generate_response_stream(history):   # normal for ✅
        full_response += chunk
        yield chunk

    add_message(user_id=user_id, role="assistant", content=full_response)