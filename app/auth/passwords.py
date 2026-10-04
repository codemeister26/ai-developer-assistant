# ─── Password hashing ─────────────────────────────────────────────────────────
# stdlib ka pbkdf2 use kar rahe hain — bcrypt/argon2 ke liye C dependency chahiye
# hoti, aur pbkdf2 OWASP ki recommended iteration count ke saath theek hai.
# Password kabhi plain store nahi hota.

import hashlib
import hmac
import os

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000      # OWASP 2023 recommendation for pbkdf2-sha256
SALT_BYTES = 16

MIN_PASSWORD_LENGTH = 8


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    """Store karne layak string: algorithm$iterations$salt$hash"""
    salt = salt or os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)

    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Timing-safe comparison — warna password guess karna aasaan ho jaata hai"""
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False

    if algorithm != ALGORITHM:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
    )

    return hmac.compare_digest(digest.hex(), digest_hex)
