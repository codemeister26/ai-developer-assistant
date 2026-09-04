# ─── Logging Setup ────────────────────────────────────────────────────────────
# Poore app ka logging ek jagah configure hota hai — har module sirf
# logging.getLogger(__name__) call karta hai, format yahin se aata hai.

import logging
from app.config.settings import LOG_LEVEL

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging():
    """App start hone par ek baar call karo — root logger configure kar deta hai"""
    logging.basicConfig(
        level=LOG_LEVEL.upper(),
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
