from ollama import Client
from app.config.settings import (
    OLLAMA_CONNECT_TIMEOUT,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_READ_TIMEOUT,
)
from app.config.prompts import get_prompt
from typing import Generator
import httpx
import logging
import time

logger = logging.getLogger(__name__)

# read timeout do chunks ke beech ka gap hai, poore jawab ka nahi — isliye lamba
# jawab bhi theek chalta hai, par Ollama chup ho jaye toh request latki nahi rehti
client = Client(
    OLLAMA_HOST,
    timeout=httpx.Timeout(
        connect=OLLAMA_CONNECT_TIMEOUT,
        read=OLLAMA_READ_TIMEOUT,
        write=OLLAMA_CONNECT_TIMEOUT,
        pool=OLLAMA_CONNECT_TIMEOUT,
    ),
)


class LLMUnavailableError(Exception):
    """Ollama se baat nahi ho payi — service layer decide karega user ko kya dikhana hai"""

def generate_response_stream(messages: list, mode: str = "general") -> Generator[str, None, None]:
    try:
        start = time.time()
        first_chunk = True

        stream = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": get_prompt(mode)},
                *messages
            ],
            stream=True,
            # Reasoning models apni soch "thinking" field mein bhejte hain aur
            # "content" khaali rakhte hain — hum sirf content stream karte hain,
            # toh user ko blank screen dikhti. Jo models thinking support nahi
            # karte, unpe ye flag bekaar hai par nuksaan nahi karta.
            think=False,
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