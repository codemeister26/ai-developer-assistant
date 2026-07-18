# def get_ai_response(message : str) -> str :
#     return f"You said {message}"

# from app.llm.ollama_client import generate_response
# def get_ai_response(message: str) -> str:
#     answer = generate_response(message)
#     return answer

from app.llm.ollama_client import generate_response
from app.memory.chat_memory import (get_history, add_message)

def get_ai_response(message: str) -> str:
    user_id = "default_user"

    add_message(
        user_id=user_id,
        role= "user",
        content=message
    )

    history = get_history(user_id)

    ai_response = generate_response(history)

    add_message(
        user_id=user_id,
        role="assistant",
        content=ai_response
    )

    return ai_response