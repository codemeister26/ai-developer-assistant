from ollama import Client
from app.config.settings import (
    OLLAMA_CONNECT_TIMEOUT,
    OLLAMA_HOST,
    OLLAMA_READ_TIMEOUT,
)
from app.llm.base import LLMProvider, LLMUnavailableError
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


class OllamaProvider(LLMProvider):
    """Local models — koi API key nahi, koi kharcha nahi"""

    def stream(self, model: str, system: str, messages: list) -> Generator[str, None, None]:
        try:
            start = time.time()
            first_chunk = True

            stream = client.chat(
                model=model,
                messages=[{"role": "system", "content": system}, *messages],
                stream=True,
                # Reasoning models apni soch "thinking" field mein bhejte hain aur
                # "content" khaali rakhte hain — hum sirf content stream karte hain,
                # toh user ko blank screen dikhti. Jo models thinking support nahi
                # karte, unpe ye flag bekaar hai par nuksaan nahi karta.
                think=False,
            )

            for chunk in stream:
                # Aakhri chunk mein token counts aate hain.
                #
                # Dhyan do: prompt_eval_count "actually evaluate kiye gaye"
                # tokens hain, "prompt mein kitne the" nahi. Wahi prompt
                # dobara bhejne par Ollama KV cache use karta hai aur count
                # kam aata hai. Local models ka cost 0 hai toh isse farak
                # nahi padta, par number dekh kar confuse mat hona.
                if chunk.get("done"):
                    self.usage = {
                        "input_tokens": chunk.get("prompt_eval_count") or 0,
                        "output_tokens": chunk.get("eval_count") or 0,
                    }

                content = chunk["message"]["content"]
                if content:
                    if first_chunk:
                        logger.info("First token time: %.2fs", time.time() - start)
                        first_chunk = False
                    yield content

            logger.info("Total time: %.2fs", time.time() - start)

        except Exception as e:
            # Error text yahan yield nahi karte — warna wo assistant ke jawab ki
            # tarah history mein save ho jaata hai
            logger.exception("Ollama request failed")
            raise LLMUnavailableError("Ollama request failed") from e
