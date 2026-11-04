from __future__ import annotations
import base64
import hashlib
import hmac
import secrets
import threading
import time
from fastapi import HTTPException, Request, status
from .db import fetchone

SESSIONS: dict[str, tuple[str, float]] = {}
SESSION_LOCK = threading.RLock()
TTL = 8 * 3600


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    hashed = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return 'scrypt$' + base64.b64encode(salt).decode() + '$' + base64.b64encode(hashed).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, b64_salt, b64_h = stored.split('$')
        if scheme != 'scrypt': return False
        salt = base64.b64decode(b64_salt)
        check = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(check, base64.b64decode(b64_h))
    except (ValueError, TypeError):
        return False


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(40)
    with SESSION_LOCK:
        SESSIONS[token] = (username, time.monotonic() + TTL)
    return token


def require_admin(request: Request) -> str:
    authorization = request.headers.get('authorization', '')
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Autenticacao obrigatoria')
    token = authorization[7:]
    with SESSION_LOCK:
        record = SESSIONS.get(token)
        if not record or record[1] < time.monotonic():
            SESSIONS.pop(token, None)
            raise HTTPException(status_code=401, detail='Sessao expirada')
        SESSIONS[token] = (record[0], time.monotonic() + TTL)
        return record[0]


def revoke(token: str):
    with SESSION_LOCK:
        SESSIONS.pop(token, None)
