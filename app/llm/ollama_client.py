from ollama import Client
from app.config.settings import OLLAMA_HOST, OLLAMA_MODEL
from app.config.prompts import DEVELOPER_ASSISTANT_PROMPT
from typing import Generator
import logging
import time

logger = logging.getLogger(__name__)

client = Client(OLLAMA_HOST)


class LLMUnavailableError(Exception):
    """Ollama se baat nahi ho payi — service layer decide karega user ko kya dikhana hai"""

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
                    logger.info("First token time: %.2fs", time.time() - start)
                    first_chunk = False
                yield content

        logger.info("Total time: %.2fs", time.time() - start)

    except Exception as e:
        # Error text yahan yield nahi karte — warna wo assistant ke jawab ki tarah
        # history mein save ho jaata hai
        logger.exception("Ollama request failed")
        raise LLMUnavailableError("Ollama request failed") from e