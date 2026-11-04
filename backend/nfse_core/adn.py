from __future__ import annotations
import base64
import gzip
import hashlib
import json
import re
import ssl
import tempfile
from contextlib import contextmanager
from pathlib import Path

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates

from .crypto import decrypt
from .identifiers import valid_tax_id
from .db import fetchone
from .settings import ADN_PRODUCTION, ADN_RESTRICTED, MAX_XML_BYTES


class AdnError(Exception):
    def __init__(self, status: int, message: str, errors: list | None = None):
        super().__init__(message)
        self.status, self.errors = status, errors or []


def load_pfx(pfx: bytes, password: str):
    private_key, cert, chain = load_key_and_certificates(pfx, password.encode() if password else None)
    if not private_key or not cert:
        raise ValueError('PFX sem certificado e chave privada')
    return private_key, cert, chain or []


@contextmanager
def _tls_context(company: dict):
    if not company.get('cert_id'):
        raise AdnError(422, 'Configure um certificado A1 antes de consultar o ADN')
    row = fetchone('SELECT * FROM certificates WHERE id=?', (company['cert_id'],))
    if not row:
        raise AdnError(422, 'Certificado nao localizado')
    private, cert, chain = load_pfx(decrypt(row['content_enc']), decrypt(row['password_enc']).decode())
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    with tempfile.TemporaryDirectory(prefix='nfse-tls-') as temp:
        keyfile = Path(temp) / 'private.pem'
        crtfile = Path(temp) / 'cert.pem'
        keyfile.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        crtfile.write_bytes(cert.public_bytes(serialization.Encoding.PEM) + b''.join(c.public_bytes(serialization.Encoding.PEM) for c in chain))
        try:
            keyfile.chmod(0o600)
            crtfile.chmod(0o600)
        except OSError:
            pass
        context.load_cert_chain(str(crtfile), str(keyfile))
        yield context


def decode_xml(encoded: str) -> bytes:
    if not isinstance(encoded, str) or len(encoded) > MAX_XML_BYTES * 2:
        raise ValueError('Documento compactado excede o limite')
    binary = base64.b64decode(encoded, validate=True)
    if len(binary) > MAX_XML_BYTES:
        raise ValueError('Documento compactado excede o limite')
    # gzip.decompress sem limite pode causar zip bomb; ler incrementalmente.
    with gzip.GzipFile(fileobj=__import__('io').BytesIO(binary)) as gz:
        xml = gz.read(MAX_XML_BYTES + 1)
    if len(xml) > MAX_XML_BYTES:
        raise ValueError('XML acima do limite permitido')
    if not xml.lstrip().startswith(b'<'):
        raise ValueError('Resposta ADN nao contem XML')
    return xml


def get_client(company: dict):
    base = ADN_PRODUCTION if company['environment'] == 'producao' else ADN_RESTRICTED
    return base


def request_adn(company_id: int, resource: str, params: dict | None = None) -> dict:
    company = fetchone('SELECT * FROM companies WHERE id=?', (company_id,))
    if not company:
        raise AdnError(404, 'Empresa nao cadastrada')
    if not resource.startswith('/') or '://' in resource or '..' in resource:
        raise AdnError(400, 'Caminho ADN nao permitido')
    with _tls_context(company) as tls:
        try:
            with httpx.Client(verify=tls, timeout=httpx.Timeout(55.0, connect=20.0), trust_env=False, follow_redirects=False) as client:
                res = client.get(get_client(company) + resource, params=params, headers={'Accept': 'application/json'})
        except (httpx.HTTPError, ssl.SSLError) as exc:
            raise AdnError(503, 'Falha na conexao TLS com ADN: ' + type(exc).__name__) from exc
    try:
        payload = res.json()
    except (json.JSONDecodeError, ValueError):
        raise AdnError(502, 'Resposta ADN nao e JSON')
    if not isinstance(payload, dict):
        raise AdnError(502, 'Formato da resposta ADN invalido')
    errors = payload.get('Erros') or []
    if res.status_code >= 400 and not (res.status_code == 404 and any(x.get('Codigo') in ('E2220','E2230','E2240') for x in errors if isinstance(x,dict))):
        raise AdnError(res.status_code, '; '.join(x.get('Codigo', '') + ': ' + x.get('Descricao', '') for x in errors if isinstance(x,dict)) or 'Erro HTTP ADN', errors)
    return {'http_status': res.status_code, **payload}


def request_nsu(company_id: int, nsu: int, batch=True, cnpj=None, cpf=None) -> dict:
    if nsu < 0:
        raise AdnError(422, 'NSU deve ser nao negativo')
    if cnpj and cpf:
        raise AdnError(422, 'cnpjConsulta e cpfConsulta sao mutuamente exclusivos')
    params = {'lote': 'true' if batch else 'false'}
    if cnpj:
        if not re.fullmatch(r'\d{14}', cnpj) or not valid_tax_id(cnpj): raise AdnError(422, 'cnpjConsulta deve conter 14 digitos validos')
        params['cnpjConsulta'] = cnpj
    if cpf:
        if not re.fullmatch(r'\d{11}', cpf) or not valid_tax_id(cpf): raise AdnError(422, 'cpfConsulta deve conter 11 digitos validos')
        params['cpfConsulta'] = cpf
    return request_adn(company_id, f'/DFe/{nsu}', params)


def request_events(company_id: int, access_key: str) -> dict:
    if not re.fullmatch(r'\d{50}', access_key):
        raise AdnError(422, 'Chave de acesso deve conter 50 digitos')
    return request_adn(company_id, f'/NFSe/{access_key}/Eventos')
