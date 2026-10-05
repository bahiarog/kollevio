import os
import time
import jwt as pyjwt
from passlib.context import CryptContext
from fastapi import Request, HTTPException

SECRET = os.getenv("SECRET_KEY", "kollevio-dev-secret-change-in-prod")
COOKIE_NAME = "kollevio_session"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False


def make_token(user_id: str, tenant_id: str, email: str, role: str) -> str:
    payload = {
        "uid": user_id,
        "tid": tenant_id,
        "email": email,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 30,
    }
    return pyjwt.encode(payload, SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return pyjwt.decode(token, SECRET, algorithms=["HS256"])


def get_current_session(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        return decode_token(token)
    except Exception:
        return None


def require_session(request: Request) -> dict:
    session = get_current_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Nicht angemeldet.")
    return session
