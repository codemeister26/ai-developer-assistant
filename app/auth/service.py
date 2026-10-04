# ─── Auth service ─────────────────────────────────────────────────────────────
# Signup, login, logout aur session lookup. Sessions opaque tokens hain jo DB
# mein rehte hain, isliye inhe kabhi bhi revoke kiya ja sakta hai.

from datetime import datetime, timedelta, timezone
import secrets

from app.auth.passwords import MIN_PASSWORD_LENGTH, hash_password, verify_password
from app.config.settings import SESSION_TTL_DAYS
from app.db.database import get_db
from app.db.models import Session as SessionRow, User

TOKEN_BYTES = 32


class AuthError(Exception):
    """Signup/login nahi ho paya — message user ko dikhaya ja sakta hai"""


def _normalise(email: str) -> str:
    return email.strip().lower()


def signup(email: str, password: str) -> str:
    """Naya user banao aur session token do"""
    email = _normalise(email)

    if not email or "@" not in email:
        raise AuthError("Enter a valid email address")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    with get_db() as db:
        if db.query(User).filter(User.email == email).first():
            raise AuthError("An account with this email already exists")

        user = User(email=email, password_hash=hash_password(password))
        db.add(user)
        db.commit()

        return _create_session(db, user.id)


def login(email: str, password: str) -> str:
    with get_db() as db:
        user = db.query(User).filter(User.email == _normalise(email)).first()

        # Email galat hai ya password — dono par ek hi message, warna attacker
        # pata kar lega ki kaun se emails registered hain
        if user is None or not verify_password(password, user.password_hash):
            raise AuthError("Email or password is incorrect")

        return _create_session(db, user.id)


def logout(token: str) -> None:
    with get_db() as db:
        db.query(SessionRow).filter(SessionRow.token == token).delete()
        db.commit()


def user_for_token(token: str) -> dict | None:
    """Token ka user do — galat ya expired token par None"""
    if not token:
        return None

    with get_db() as db:
        session = db.query(SessionRow).filter(SessionRow.token == token).first()

        if session is None:
            return None

        if session.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            db.delete(session)
            db.commit()
            return None

        user = db.query(User).filter(User.id == session.user_id).first()
        return {"id": user.id, "email": user.email} if user else None


def _create_session(db, user_id: int) -> str:
    token = secrets.token_urlsafe(TOKEN_BYTES)
    expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        days=SESSION_TTL_DAYS
    )

    db.add(SessionRow(token=token, user_id=user_id, expires_at=expires))
    db.commit()
    return token
