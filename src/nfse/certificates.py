"""A1 PKCS#12 validation and encrypted storage. Never log private keys."""
from __future__ import annotations
from contextlib import contextmanager
import base64
from datetime import timezone, datetime
import hashlib
import os
from pathlib import Path
import ssl
import tempfile
from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from .settings import ensure_data_dir
from .store import Store, now


class CertificateVault:
    def __init__(self, store: Store):
        self.store = store
        self.keyfile = ensure_data_dir() / 'credential.key'
        if not self.keyfile.exists():
            try:
                with self.keyfile.open('xb') as output:
                    output.write(Fernet.generate_key())
                if os.name != 'nt':
                    self.keyfile.chmod(0o600)
            except FileExistsError:
                pass
        self.crypt = Fernet(self.keyfile.read_bytes().strip())

    def add(self, label: str, pfx_data: str, password: str):
        if len(pfx_data) > 4*1024*1024:
            raise ValueError('Certificado excede o tamanho permitido.')
        try:
            pfx = base64.b64decode(pfx_data, validate=True)
        except Exception:
            raise ValueError('Certificado deve ser PFX/P12 codificado em Base64.') from None
        if len(pfx) > 2*1024*1024:
            raise ValueError('Certificado excede 2 MB.')
        private, cert, chain = load_key_and_certificates(pfx, password.encode())
        if private is None or cert is None:
            raise ValueError('PFX sem certificado e chave privada.')
        if cert.not_valid_after_utc < datetime.now(timezone.utc):
            raise ValueError('Certificado expirado.')
        try:
            uses = cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
            if ExtendedKeyUsageOID.CLIENT_AUTH not in uses and ExtendedKeyUsageOID.ANY_EXTENDED_KEY_USAGE not in uses:
                raise ValueError('Certificado sem finalidade de autenticação do cliente.')
        except x509.ExtensionNotFound:
            pass  # A ausência de EKU não prova que a cadeia será rejeitada pelo ADN.
        fingerprint = cert.fingerprint(hashes.SHA256()).hex()
        subject = cert.subject.rfc4514_string()
        identity = ''
        for entry in cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME):
            identity = entry.value[:200]
        with self.store.transaction() as db:
            cur = db.execute('INSERT INTO certificates(label,identity,serial_number,subject,expires_at,encrypted_pfx,encrypted_password,sha256,created_at) '
                             'VALUES(?,?,?,?,?,?,?,?,?)',
                             (label.strip()[:120],identity,str(cert.serial_number),subject,
                              cert.not_valid_after_utc.isoformat(),self.crypt.encrypt(pfx),
                              self.crypt.encrypt(password.encode()),fingerprint,now()))
            key = cur.lastrowid
        return {'id':key,'label':label,'identity':identity,'expires_at':cert.not_valid_after_utc.isoformat()}

    @contextmanager
    def client_context(self, certificate_id: int):
        record = self.store.row('SELECT * FROM certificates WHERE id=?',(certificate_id,))
        if not record: raise ValueError('Certificado não encontrado.')
        pfx = self.crypt.decrypt(record['encrypted_pfx'])
        password = self.crypt.decrypt(record['encrypted_password'])
        private, cert, chain = load_key_and_certificates(pfx, password)
        if not private or not cert: raise ValueError('Certificado sem chave privada.')
        if cert.not_valid_after_utc <= datetime.now(timezone.utc):
            raise ValueError('Certificado expirado.')
        # File descriptors use a private directory, removed immediately after SSLContext.load_cert_chain.
        with tempfile.TemporaryDirectory(prefix='nfse-mtls-') as folder:
            cert_path = Path(folder)/'cert.pem'
            key_path = Path(folder)/'key.pem'
            cert_bytes = cert.public_bytes(serialization.Encoding.PEM)
            for extra in chain or []: cert_bytes += extra.public_bytes(serialization.Encoding.PEM)
            cert_path.write_bytes(cert_bytes)
            key_path.write_bytes(private.private_bytes(serialization.Encoding.PEM,
                                 serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
            if os.name != 'nt':
                cert_path.chmod(0o600)
                key_path.chmod(0o600)
            context = ssl.create_default_context()
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(str(cert_path),str(key_path))
        yield context
