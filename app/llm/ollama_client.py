from ollama import Client
from app.config.settings import OLLAMA_HOST, OLLAMA_MODEL
from app.config.prompts import DEVELOPER_ASSISTANT_PROMPT
import time

# Initialize client once
client = Client(OLLAMA_HOST)

def generate_response(messages: list) -> str:
    try:
        start = time.time()
        
        response = client.chat(
            model=OLLAMA_MODEL,
                    messages=[
            {
                "role": "system",
                "content": DEVELOPER_ASSISTANT_PROMPT
            },
            *messages
        ]
        )
        
        end = time.time()
        print(f"Time Taken: {end - start:.2f} seconds")
        
        return response["message"]["content"]
    
    except Exception as e:
        print(f"Ollama Error: {e}")
        return "AI service is currently unavailable."
