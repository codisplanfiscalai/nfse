import base64
import gzip
from pathlib import Path
import pytest


def bootstrap_app(tmp_path,monkeypatch):
    monkeypatch.setenv('CODISPLAN_DATA_DIR',str(tmp_path))
    from nfse_core import db, crypto
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'test.sqlite3')
    monkeypatch.setattr(crypto, 'KEY_PATH', tmp_path / 'test.key')
    db.init_db()
    from nfse_core.api import app
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_auth_and_reports(tmp_path,monkeypatch):
    client=bootstrap_app(tmp_path,monkeypatch)
    assert client.get('/api/bootstrap/status').json()['needs_setup']
    assert client.post('/api/bootstrap',json={'username':'admin','password':'senha-segura-2026'}).status_code==200
    assert client.post('/api/bootstrap',json={'username':'outro','password':'senha-segura-2026'}).status_code==409
    assert client.get('/api/companies').status_code==401
    r=client.post('/api/auth/login',json={'username':'admin','password':'senha-segura-2026'})
    assert r.status_code==200
    auth={'Authorization':'Bearer '+r.json()['token']}
    r=client.post('/api/companies',json={'name':'Empresa Exemplo','tax_id':'11222333000181','environment':'restrita'},headers=auth)
    assert r.status_code==200
    company_id=r.json()['id']
    from nfse_core.storage import import_one
    xml=Path(__file__).with_name('nfse_exemplo.xml').read_bytes()
    key=__import__('re').search(r'NFS(\d{50})',xml.decode()).group(1)
    entry={'NSU':1,'ChaveAcesso':key,'TipoDocumento':'NFSE','ArquivoXml':base64.b64encode(gzip.compress(xml)).decode()}
    assert import_one(company_id,entry) is True
    assert import_one(company_id,entry) is False
    rep_path=f'/api/companies/{company_id}/reports?start=2026-11-01&end=2026-11-30&basis=issued&kind=mensal'
    result=client.get(rep_path,headers=auth)
    assert result.status_code==200,result.text
    assert result.json()['summary']['count']==1
    assert result.json()['summary']['totals']['amount_cents']=='1.000,00'
    for fmt,ctype in [('xlsx','spreadsheet'),('pdf','pdf'),('csv','csv')]:
        result=client.get(rep_path+'&format='+fmt,headers=auth)
        assert result.status_code==200,result.text[:100]
        assert ctype in result.headers['content-type']
        assert len(result.content)>500
    r=client.get('/api/companies/'+str(company_id)+'/documents',headers=auth)
    assert len(r.json())==1
    r=client.get('/api/companies/'+str(company_id)+'/documents/'+str(r.json()[0]['id'])+'/xml',headers=auth)
    assert r.content==xml


def test_cancel_event_and_iss_filter(tmp_path,monkeypatch):
    client=bootstrap_app(tmp_path,monkeypatch)
    # DB de teste isolado do outro processo.
    from nfse_core.db import connect
    from nfse_core.storage import import_one
    with connect() as c:
        c.execute('INSERT INTO companies(name,tax_id) VALUES (?,?)',('Empresa','11222333000181'))
        company=c.execute('SELECT id FROM companies LIMIT 1').fetchone()[0]
    xml=Path(__file__).with_name('nfse_exemplo.xml').read_bytes()
    import re
    key=re.search(r'NFS(\d{50})',xml.decode()).group(1)
    invoice={'NSU':8,'ChaveAcesso':key,'TipoDocumento':'NFSE','ArquivoXml':base64.b64encode(gzip.compress(xml)).decode()}
    import_one(company,invoice)
    def rep(kind):
        from nfse_core.reports import query_report
        return query_report(company,'2026-11-01','2026-11-30','issued',kind)
    assert rep('mensal')[0]['count']==1
    assert rep('iss_retido')[0]['count']==0 # fixture tpRetISSQN=1 (nao retido)
    event={'NSU':9,'ChaveAcesso':key,'TipoDocumento':'EVENTO','TipoEvento':'CANCELAMENTO',
         'ArquivoXml':base64.b64encode(gzip.compress(b'<evento>cancelamento</evento>')).decode()}
    import_one(company,event)
    assert rep('canceladas')[0]['count']==1
    assert rep('mensal')[0]['count']==0
    assert import_one(company,event) is False


def test_nsu_parameters_and_decode(monkeypatch):
    from nfse_core.adn import request_nsu, AdnError,decode_xml
    with pytest.raises(AdnError):request_nsu(1,0,cnpj='01234567890123',cpf='12345678901')
    with pytest.raises(AdnError):request_nsu(1,-1)
    with pytest.raises(Exception):decode_xml(base64.b64encode(b'notgzip').decode())


def test_nsu_sync_with_mocked_official_response(tmp_path,monkeypatch):
    bootstrap_app(tmp_path,monkeypatch)
    from nfse_core.db import connect,fetchone
    from nfse_core import sync
    with connect() as c:
        c.execute("INSERT INTO companies(name,tax_id,cert_id) VALUES (?,?,?)",('Cliente','11222333000181',1))
        cid=c.execute('SELECT id FROM companies ORDER BY id DESC LIMIT 1').fetchone()[0]
        c.execute('INSERT INTO cursors(company_id) VALUES (?)',(cid,))
    xml=Path(__file__).with_name('nfse_exemplo.xml').read_bytes()
    import re
    key=re.search(r'NFS(\d{50})',xml.decode()).group(1)
    calls=[]
    def fake_request(company_id,nsu,batch,cnpj=None,cpf=None):
        calls.append(nsu)
        if nsu==0:
            return {'http_status':200,'StatusProcessamento':'DOCUMENTOS_LOCALIZADOS',
               'TipoConsulta':'CnpjBase', 'LoteDFe':[{'NSU':10,'ChaveAcesso':key,'TipoDocumento':'NFSE',
                'ArquivoXml':base64.b64encode(gzip.compress(xml)).decode()}]}
        return {'http_status':404,'StatusProcessamento':'NENHUM_DOCUMENTO_LOCALIZADO','Erros':[{'Codigo':'E2220'}]}
    monkeypatch.setattr(sync,'request_nsu',fake_request)
    result=sync.sync_company(cid)
    assert result=={'imported':1,'nsu':10}
    assert calls==[0,10]
    assert fetchone('SELECT nsu,status FROM cursors WHERE company_id=?',(cid,))=={'nsu':10,'status':'ok'}
    assert sync.sync_company(cid)['imported']==0


def test_event_arrives_before_invoice(tmp_path,monkeypatch):
    bootstrap_app(tmp_path,monkeypatch)
    from nfse_core.db import connect,fetchone
    from nfse_core.storage import import_one
    with connect() as c:
        c.execute('INSERT INTO companies(name,tax_id) VALUES (?,?)',('Cliente','11222333000181'))
        cid=c.execute('SELECT id FROM companies ORDER BY id DESC LIMIT 1').fetchone()[0]
    xml=Path(__file__).with_name('nfse_exemplo.xml').read_bytes()
    import re
    key=re.search(r'NFS(\d{50})',xml.decode()).group(1)
    event={'NSU':5,'ChaveAcesso':key,'TipoDocumento':'EVENTO','TipoEvento':'CANCELAMENTO_POR_SUBSTITUICAO',
       'ArquivoXml':base64.b64encode(gzip.compress(b'<evento>substituicao</evento>')).decode()}
    invoice={'NSU':6,'ChaveAcesso':key,'TipoDocumento':'NFSE','ArquivoXml':base64.b64encode(gzip.compress(xml)).decode()}
    import_one(cid,event)
    import_one(cid,invoice)
    status=fetchone('SELECT status FROM invoices WHERE company_id=?',(cid,))
    assert status['status']=='substituida'


def test_tax_identifiers():
    from nfse_core.identifiers import valid_tax_id
    assert valid_tax_id('11.222.333/0001-81')
    assert not valid_tax_id('11.222.333/0001-82')
    assert not valid_tax_id('000.000.000-00')
