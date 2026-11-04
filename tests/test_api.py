from __future__ import annotations
import base64,gzip,io,json,ssl,sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from src.nfse.api import build_app
from src.nfse.store import Store
from src.nfse.adn import AdnClient,AdnError,decode_xml,validate_base_url
from src.nfse.xml_documents import normalize
from src.nfse.reports import query_report,pdf,excel,csv_bytes

XML=b'''<?xml version="1.0"?><NFSe xmlns="http://www.sped.fazenda.gov.br/nfse"><infNFSe><nNFSe>134</nNFSe><dhProc>2026-11-04T12:00:00-03:00</dhProc><emit><CNPJ>11222333000181</CNPJ><xNome>Empresa</xNome></emit><valores><vISSQN>20</vISSQN><vISSRet>20</vISSRet><vLiq>900</vLiq></valores><DPS><infDPS><dhEmi>2026-11-04T09:00:00-03:00</dhEmi><dCompet>2026-10-01</dCompet><toma><CNPJ>12345678000190</CNPJ><xNome>Cliente A</xNome></toma><serv><cServ><cTribNac>010101</cTribNac><xDescServ>Consultoria Fiscal</xDescServ></cServ></serv><valores><vServPrest><vServ>1000</vServ></vServPrest><trib><tribFed><vRetIRRF>15</vRetIRRF><vRetCSLL>45</vRetCSLL></tribFed></trib></valores></infDPS></DPS></infNFSe></NFSe>'''

def example(nsu=1,key='A'*44,kind='NFSE',event=None,xml=XML):
    return normalize({'NSU':nsu,'ChaveAcesso':key,'TipoDocumento':kind,'TipoEvento':event,
                      'DataHoraGeracao':'2026-11-04T12:00:00-03:00'},xml)

@pytest.fixture()
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('NFSE_DATA_DIR',str(tmp_path/'data'))
    store=Store(tmp_path/'nfse.sqlite3')
    c=TestClient(build_app(store,worker=False))
    assert c.post('/api/v1/setup',json={'name':'Responsável','email':'admin@example.test','password':'long-test-password-123'}).status_code==200
    login=c.post('/api/v1/auth/login',json={'email':'admin@example.test','password':'long-test-password-123'})
    assert login.status_code==200
    c.headers['X-CSRF-Token']=login.json()['data']['csrf']
    return c,store

def test_setup_and_auth(client):
    c,s=client
    assert c.get('/api/v1/auth/me').status_code==200
    assert c.post('/api/v1/setup',json={'name':'x','email':'x@y','password':'long-test-password'}).status_code==409
    assert c.post('/api/v1/companies',json={'name':'Emissor','identifier':'11222333000181'}).status_code==200
    assert len(c.get('/api/v1/companies').json()['data'])==1
    assert c.get('/api/v1/dashboard').json()['data']['companies']==1
    c.headers['X-CSRF-Token']='invalido'
    assert c.post('/api/v1/companies',json={'name':'Outra','identifier':'22222222000111'}).status_code==403

def test_login_fail(client):
    c,_=client
    with TestClient(c.app) as other:
        for _ in range(8):assert other.post('/api/v1/auth/login',json={'email':'admin@example.test','password':'bad'}).status_code==401
        assert other.post('/api/v1/auth/login',json={'email':'admin@example.test','password':'bad'}).status_code==429

def test_adn_contract():
    assert validate_base_url('https://www.nfse.gov.br/api')=='https://www.nfse.gov.br/api'
    with pytest.raises(ValueError):validate_base_url('http://localhost:8000')
    with pytest.raises(ValueError):validate_base_url('https://evil.example')
    with pytest.raises(ValueError):AdnClient('https://x.nfse.gov.br',ssl.create_default_context()).by_nsu(1,cnpj='123',cpf='123')
    assert decode_xml(base64.b64encode(gzip.compress(XML)).decode())==XML
    with pytest.raises(AdnError):decode_xml('invalid gzip')

def test_import_idempotency_cancel_and_reporting(client):
    c,store=client
    company=c.post('/api/v1/companies',json={'name':'Emissor','identifier':'11222333000181'}).json()['data']['id']
    with store.transaction() as db:
        db.execute("INSERT INTO certificates(id,label,encrypted_pfx,encrypted_password,sha256,created_at) VALUES(1,'a',X'01',X'02','h','now')")
    inserted,last=store.apply_documents(company,1,[example()]);assert (inserted,last)==(1,1)
    inserted,last=store.apply_documents(company,1,[example()]);assert (inserted,last)==(0,1)
    report=query_report(store,company,'competencia','2026-10-01','2026-10-31')
    assert report['count']==1 and report['totals']['service_cents']==100000
    assert pdf(report)[:4]==b'%PDF' and excel(report)[:2]==b'PK'
    assert b'Consultoria Fiscal' in csv_bytes(report)
    assert query_report(store,company,'mensal','2026-10-01','2026-10-31')['count']==0
    cancellation=b'<evento><tpEvento>CANCELAMENTO</tpEvento></evento>'
    store.apply_documents(company,1,[example(2,kind='EVENTO',event='CANCELAMENTO',xml=cancellation)])
    status=store.row("SELECT status FROM documents WHERE document_type='NFSE'")
    assert status['status']=='CANCELADA'
    report=query_report(store,company,'competencia','2026-10-01','2026-10-31')
    assert report['totals']['service_cents']==0
    assert query_report(store,company,'canceladas','2026-11-01','2026-11-30')['count']==1

def test_report_api_and_csp(client):
    c,store=client
    r=c.post('/api/v1/companies',json={'name':'Emissor','identifier':'11222333000181'})
    cid=r.json()['data']['id']
    with store.transaction() as db:db.execute("INSERT INTO certificates(id,label,encrypted_pfx,encrypted_password,sha256,created_at) VALUES(1,'a',X'01',X'02','h','now')")
    store.apply_documents(cid,1,[example()])
    url=f'/api/v1/reports/competencia?company_id={cid}&inicio=2026-10-01&fim=2026-10-31'
    assert c.get(url).json()['data']['count']==1
    assert c.get(url+'&formato=pdf').content.startswith(b'%PDF')
    assert c.get(url+'&formato=xlsx').content.startswith(b'PK')
    assert c.get('/').status_code==200
    assert "unsafe-eval" not in c.get('/').headers['content-security-policy']

