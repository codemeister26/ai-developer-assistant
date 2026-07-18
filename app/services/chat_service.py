from app.llm.ollama_client import generate_response_stream
from app.memory.chat_memory import get_history, add_message
from typing import Generator
import uuid

def get_ai_response_stream(message: str, conversation_id:str = None) -> Generator[str, None, None]:
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    add_message(conversation_id=conversation_id, role="user", content=message)

    history = get_history(conversation_id)
    full_response = ""

    for chunk in generate_response_stream(history):   # normal for ✅
        full_response += chunk
        yield chunk

    add_message(conversation_id=conversation_id, role="assistant", content=full_response)