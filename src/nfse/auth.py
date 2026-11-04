"""Local sessions, password hashing, CSRF and API tokens."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import hmac
import os
import secrets
import time
from .store import Store, now


class AuthError(Exception):
    def __init__(self, message='Acesso não autorizado.', status=401):
        super().__init__(message)
        self.status = status


def hash_password(password: str) -> str:
    if len(password) < 12 or len(password) > 1024:
        raise ValueError('A senha deve conter entre 12 e 1024 caracteres.')
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f'scrypt$16384${salt.hex()}${digest.hex()}'


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, cost, salt, expected = encoded.split('$')
        if algo != 'scrypt' or cost != '16384':
            return False
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1)
        return hmac.compare_digest(digest, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class Identity:
    def __init__(self, store: Store):
        self.store = store
        self.attempts = {}

    def configured(self):
        return self.store.row('SELECT id FROM users LIMIT 1') is not None

    def setup(self, name: str, email: str, password: str):
        if not name.strip() or not email.strip() or '@' not in email:
            raise ValueError('Informe nome e e-mail válidos.')
        encoded = hash_password(password)
        with self.store.transaction() as conn:
            if conn.execute('SELECT id FROM users LIMIT 1').fetchone():
                raise AuthError('Ambiente já configurado.', 409)
            conn.execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',
                         (name.strip(), email.strip().lower(), encoded, 'admin', now()))
        self.store.audit('sistema', 'setup', 'admin')
        return {'ok': True}

    def login(self, email: str, password: str, ip: str):
        key = f'{ip}:{email.lower()}'
        current = time.monotonic()
        attempts = [t for t in self.attempts.get(key, []) if current-t < 900]
        if len(attempts) >= 8:
            raise AuthError('Muitas tentativas. Tente novamente posteriormente.', 429)
        user = self.store.row('SELECT * FROM users WHERE email=? AND active=1', (email.strip().lower(),))
        if user is None or not verify_password(password, user['password_hash']):
            attempts.append(current)
            self.attempts[key] = attempts
            raise AuthError('Credenciais inválidas.')
        self.attempts.pop(key, None)
        token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
        expiry = int(time.time()) + 8*3600
        with self.store.transaction() as conn:
            conn.execute('DELETE FROM sessions WHERE expires_at < ?', (int(time.time()),))
            conn.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',
                         (digest(token),user['id'],digest(csrf),expiry,now()))
        self.store.audit(str(user['id']), 'login', 'session')
        return token, csrf, self.public_user(user)

    @staticmethod
    def public_user(user):
        return {'id':user['id'],'name':user['name'],'email':user['email'],'role':user['role']}

    def authorize(self, token: str):
        if not token:
            raise AuthError()
        row = self.store.row('SELECT u.id,u.name,u.email,u.role,u.active,s.expires_at FROM sessions s '
                             'JOIN users u ON u.id=s.user_id WHERE s.token_hash=?', (digest(token),))
        if not row or not row['active'] or row['expires_at'] < int(time.time()):
            raise AuthError()
        return self.public_user(row)

    def check_csrf(self, token: str, csrf: str):
        row = self.store.row('SELECT csrf_hash FROM sessions WHERE token_hash=?', (digest(token),))
        if not row or not csrf or not hmac.compare_digest(row['csrf_hash'], digest(csrf)):
            raise AuthError('Proteção de formulário inválida.',403)

    def bearer(self, token: str):
        row = self.store.row('SELECT u.id,u.name,u.email,u.role,u.active,t.expires_at FROM api_tokens t '
                             'JOIN users u ON u.id=t.user_id WHERE t.token_hash=? AND t.revoked=0', (digest(token),))
        if not row or not row['active'] or row['expires_at'] < int(time.time()):
            raise AuthError()
        return self.public_user(row)

    def create_token(self, user, name, days=30):
        if not 1 <= int(days) <= 365:
            raise ValueError('Validade deve estar entre 1 e 365 dias.')
        token = secrets.token_urlsafe(48)
        with self.store.transaction() as conn:
            conn.execute('INSERT INTO api_tokens(name,token_hash,user_id,created_at,expires_at) VALUES(?,?,?,?,?)',
                         (str(name)[:120],digest(token),user['id'],now(),int(time.time())+int(days)*86400))
        self.store.audit(str(user['id']),'api_token_created',str(name))
        return {'token':token,'name':name,'expires_in_days':days}
