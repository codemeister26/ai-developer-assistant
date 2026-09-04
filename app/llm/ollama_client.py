from ollama import Client
from app.config.settings import OLLAMA_HOST, OLLAMA_MODEL
from app.config.prompts import DEVELOPER_ASSISTANT_PROMPT
from typing import Generator
import logging
import time

logger = logging.getLogger(__name__)

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
                    logger.info("First token time: %.2fs", time.time() - start)
                    first_chunk = False
                yield content

        logger.info("Total time: %.2fs", time.time() - start)

    except Exception:
        logger.exception("Ollama request failed")
        yield "AI service is currently unavailable."