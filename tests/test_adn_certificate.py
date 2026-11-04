"""ADN contract, encrypted A1 vault, and direct queries without cursor skipping."""
from __future__ import annotations
import base64
import gzip
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import ssl
import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization.pkcs12 import serialize_key_and_certificates
from cryptography.x509.oid import NameOID,ExtendedKeyUsageOID
import pytest
from src.nfse.adn import AdnClient,AdnError
from src.nfse.certificates import CertificateVault
from src.nfse.store import Store
from src.nfse.sync import Synchronizer
from tests.test_api import XML


def create_pfx():
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Empresa de Teste')])
    cert=(x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
          .public_key(key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(datetime.now(timezone.utc)-timedelta(days=1))
          .not_valid_after(datetime.now(timezone.utc)+timedelta(days=10))
          .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),critical=False)
          .sign(key,hashes.SHA256()))
    return serialize_key_and_certificates(b'Empresa',key,cert,None,
                              serialization.BestAvailableEncryption(b'segredo'))


def test_certificates_encrypted_and_context(tmp_path,monkeypatch):
    monkeypatch.setenv('NFSE_DATA_DIR',str(tmp_path/'files'))
    store=Store(tmp_path/'base.db')
    vault=CertificateVault(store)
    pfx=create_pfx()
    record=vault.add('Certificado de teste',base64.b64encode(pfx).decode(),'segredo')
    row=store.row('SELECT * FROM certificates WHERE id=?',(record['id'],))
    assert pfx not in row['encrypted_pfx']
    with vault.client_context(record['id']) as context:
        assert context.minimum_version>=ssl.TLSVersion.TLSv1_2
    with pytest.raises(Exception):vault.add('Invalido',base64.b64encode(pfx).decode(),'senha-errada')


def test_adn_all_query_modes():
    calls=[]
    payload={'StatusProcessamento':'DOCUMENTOS_LOCALIZADOS','TipoConsulta':'Procuracao','LoteDFe':[
        {'NSU':4,'ChaveAcesso':'A'*44,'TipoDocumento':'NFSE','ArquivoXml':base64.b64encode(gzip.compress(XML)).decode()}]}
    def respond(request):
        calls.append((request.url.path,dict(request.url.params)))
        return httpx.Response(200,json=payload)
    client=AdnClient('https://example.nfse.gov.br/api',ssl.create_default_context(),transport=httpx.MockTransport(respond))
    assert client.by_nsu(3,cnpj='11222333000181')['LoteDFe'][0]['NSU']==4
    assert calls[0][0]=='/api/DFe/3' and calls[0][1]['lote']=='true' and calls[0][1]['cnpjConsulta']=='11222333000181'
    assert client.by_nsu(4,cpf='12345678901',lote=False)['LoteDFe'][0]['NSU']==4
    assert calls[1][1]['lote']=='false' and calls[1][1]['cpfConsulta']=='12345678901'
    assert client.events('A'*44)['StatusProcessamento']=='DOCUMENTOS_LOCALIZADOS'
    assert calls[2][0]=='/api/NFSe/'+('A'*44)+'/Eventos'


def test_official_error_codes():
    payload={'StatusProcessamento':'REJEICAO','Erros':[{'Codigo':'E2245','Descricao':'Procuração ausente.'}]}
    def respond(request):return httpx.Response(400,json=payload)
    client=AdnClient('https://example.nfse.gov.br',ssl.create_default_context(),transport=httpx.MockTransport(respond))
    with pytest.raises(AdnError) as err:client.by_nsu(0,cnpj='11222333000181')
    assert err.value.codes[0]['code']=='E2245'
    def empty(request):return httpx.Response(404,json={'StatusProcessamento':'NENHUM_DOCUMENTO_LOCALIZADO','Erros':[{'Codigo':'E2220','Descricao':'Nenhum.'}]})
    client=AdnClient('https://example.nfse.gov.br',ssl.create_default_context(),transport=httpx.MockTransport(empty))
    assert client.by_nsu(10)['LoteDFe']==[]


def test_manual_import_does_not_move_nsu_cursor(tmp_path):
    from tests.test_api import example
    store=Store(tmp_path/'base.db')
    with store.transaction() as db:
        db.execute("INSERT INTO companies(id,name,identifier,created_at) VALUES(1,'Emitente','11222333000181','now')")
        db.execute("INSERT INTO certificates(id,label,encrypted_pfx,encrypted_password,sha256,created_at) VALUES(1,'a',X'01',X'02','h','now')")
    store.apply_documents(1,1,[example(20)],advance=False)
    assert store.row('SELECT last_nsu FROM sync_cursors WHERE company_id=1') is None
    store.apply_documents(1,1,[example(1,key='B'*44)],advance=True)
    assert store.row('SELECT last_nsu FROM sync_cursors WHERE company_id=1')['last_nsu']==1
