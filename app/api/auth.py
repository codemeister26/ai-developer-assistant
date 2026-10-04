from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.auth import service
from app.auth.service import AuthError
from app.config.settings import AUTH_ENABLED

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class Credentials(BaseModel):
    email: str = Field(..., max_length=200)
    password: str = Field(..., max_length=200)


class SessionOut(BaseModel):
    token: str
    email: str


class AuthStatus(BaseModel):
    """Frontend isse decide karta hai ki login screen dikhani hai ya nahi"""
    enabled: bool
    email: str | None = None


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        return ""
    return authorization[7:].strip()


def current_user(authorization: str | None = Header(default=None)) -> dict | None:
    """Logged-in user, ya None.

    Auth band ho toh hamesha None — app single-user mode mein chalti hai aur
    koi bhi endpoint block nahi hota.
    """
    if not AUTH_ENABLED:
        return None

    user = service.user_for_token(_bearer(authorization))

    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to continue")

    return user


@router.get("/status", response_model=AuthStatus)
def status(authorization: str | None = Header(default=None)):
    """Auth on hai ya nahi, aur abhi kaun logged in hai"""
    if not AUTH_ENABLED:
        return {"enabled": False}

    user = service.user_for_token(_bearer(authorization))
    return {"enabled": True, "email": user["email"] if user else None}


@router.post("/signup", response_model=SessionOut)
def signup(credentials: Credentials):
    try:
        token = service.signup(credentials.email, credentials.password)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"token": token, "email": credentials.email.strip().lower()}


@router.post("/login", response_model=SessionOut)
def login(credentials: Credentials):
    try:
        token = service.login(credentials.email, credentials.password)
    except AuthError as e:
        # 401 isliye — ye credentials ka masla hai, request ki shape ka nahi
        raise HTTPException(status_code=401, detail=str(e))

    return {"token": token, "email": credentials.email.strip().lower()}


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    service.logout(_bearer(authorization))
    return {"message": "Signed out"}
