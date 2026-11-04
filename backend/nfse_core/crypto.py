"""Protecao local: chave protegida com DPAPI no Windows; no Docker, CODISPLAN_MASTER_KEY obrigatoria.

A pasta de dados da instalacao Windows deve receber ACL exclusiva de SYSTEM/Administrators;
DPAPI LocalMachine nao substitui ACL correta. Nao registramos material criptografico em logs.
"""
from __future__ import annotations
import base64
import os
from pathlib import Path
from cryptography.fernet import Fernet
from .settings import ROOT

KEY_PATH = ROOT / 'key.bin'


def _key():
    explicit = os.getenv('CODISPLAN_MASTER_KEY')
    if explicit:
        return explicit.encode('ascii')
    if os.name != 'nt':
        # Chave de maquina apenas para desenvolvimento local. Container deve usar segredo externo.
        if os.getenv('CODISPLAN_REQUIRE_EXTERNAL_KEY') == '1':
            raise RuntimeError('Configure CODISPLAN_MASTER_KEY no ambiente de producao')
        if not KEY_PATH.exists():
            KEY_PATH.write_bytes(Fernet.generate_key())
            KEY_PATH.chmod(0o600)
        return KEY_PATH.read_bytes().strip()
    import win32crypt
    if KEY_PATH.exists():
        return win32crypt.CryptUnprotectData(KEY_PATH.read_bytes(), None, None, None, 0)[1]
    key = Fernet.generate_key()
    blob = win32crypt.CryptProtectData(key, 'Codisplan NFS-e', None, None, None, win32crypt.CRYPTPROTECT_LOCAL_MACHINE)
    KEY_PATH.write_bytes(blob)
    return key


def encrypt(raw: bytes) -> bytes:
    return Fernet(_key()).encrypt(raw)


def decrypt(raw: bytes) -> bytes:
    return Fernet(_key()).decrypt(raw)
