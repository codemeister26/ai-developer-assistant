from ollama import Client
from app.config.settings import OLLAMA_HOST, OLLAMA_MODEL
from app.config.prompts import DEVELOPER_ASSISTANT_PROMPT
from typing import Generator
import time

client = Client(OLLAMA_HOST)

def generate_response_stream(messages: list) -> Generator[str, None, None]:
    try:
        start = time.time()
        first_chunk = True

        stream = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": DEVELOPER_ASSISTANT_PROMPT},
                *messages
            ],
            stream=True
        )

        for chunk in stream:
            content = chunk["message"]["content"]
            if content:
                if first_chunk:
                    print(f"⏱ First token time: {time.time() - start:.2f}s")
                    first_chunk = False
                yield content

        print(f"⏱ Total time: {time.time() - start:.2f}s")

    except Exception as e:
        print(f"Ollama Error: {e}")
        yield "AI service is currently unavailable."