import anthropic

from app.config.settings import ANTHROPIC_MAX_TOKENS
from app.llm.base import LLMAuthError, LLMProvider, LLMUnavailableError
from app.llm.models import get_model
from typing import Generator
import logging
import time

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Claude models — user apni API key laata hai (BYOK).

    Key kabhi save nahi hoti: har request ke saath aati hai, client banane ke
    liye use hoti hai, aur request khatam hote hi chali jaati hai.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise LLMAuthError("Claude models ke liye API key chahiye")

        self.api_key = api_key

    def stream(self, model: str, system: str, messages: list) -> Generator[str, None, None]:
        client = anthropic.Anthropic(api_key=self.api_key)
        info = get_model(model)
        extra = dict(info.extra_params) if info else {}

        try:
            start = time.time()
            first_chunk = True

            # text_stream sirf jawab ka text deta hai — thinking blocks apne aap
            # bahar reh jaate hain, isliye reasoning ke dauran kachra nahi aata
            with client.messages.stream(
                model=model,
                max_tokens=ANTHROPIC_MAX_TOKENS,
                system=system,
                messages=messages,
                **extra,
            ) as stream:
                for text in stream.text_stream:
                    if text:
                        if first_chunk:
                            logger.info("First token time: %.2fs", time.time() - start)
                            first_chunk = False
                        yield text

            logger.info("Total time: %.2fs", time.time() - start)

        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            # Ise alag rakhna zaruri hai — user apni key theek karke retry kar sakta hai
            logger.warning("Anthropic rejected the API key: %s", type(e).__name__)
            raise LLMAuthError("API key galat hai ya usme permission nahi hai") from e

        except anthropic.APIStatusError as e:
            logger.warning("Anthropic API error %s", e.status_code)
            raise LLMUnavailableError(f"Anthropic API error ({e.status_code})") from e

        except anthropic.APIConnectionError as e:
            logger.warning("Anthropic tak pahunch nahi paye")
            raise LLMUnavailableError("Anthropic tak pahunch nahi paye") from e

        except Exception as e:
            # Poora exception log nahi karte — usme request body aur key aa sakti hai
            logger.warning("Anthropic request failed: %s", type(e).__name__)
            raise LLMUnavailableError("Anthropic request failed") from e
