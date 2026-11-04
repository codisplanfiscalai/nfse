from __future__ import annotations
import base64
import hashlib
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Literal

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from fastapi import FastAPI, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .settings import ROOT, DB_PATH
from .db import init_db, fetchone, fetchall, connect, audit
from .auth import hash_password, verify_password, create_session, require_admin, revoke
from .adn import AdnError, request_nsu, request_events
from .storage import import_lote, import_one
from .crypto import encrypt, decrypt
from .reports import query_report, as_csv, as_xlsx, as_pdf, as_json
from .sync import queue_sync, JOBS, Scheduler
from .identifiers import valid_tax_id

scheduler=Scheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    yield
    scheduler.stop()

app=FastAPI(title='Codisplan NFS-e API',version='0.1.2',docs_url=None,redoc_url=None,lifespan=lifespan)

@app.middleware('http')
async def security_headers(request:Request,call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    return response

@app.exception_handler(AdnError)
async def adn_exception(request:Request,exc:AdnError):
    return JSONResponse(status_code=exc.status if 400<=exc.status<=599 else 502,content={'detail':str(exc),'errors':exc.errors})

class Boot(BaseModel):
    username:str=Field(min_length=3,max_length=60)
    password:str=Field(min_length=12,max_length=200)

class Login(BaseModel):
    username:str
    password:str

class CompanyIn(BaseModel):
    name:str=Field(min_length=2,max_length=250)
    tax_id:str=Field(min_length=11,max_length=18)
    environment:Literal['restrita','producao']='restrita'
    active:bool=True

class AssignCert(BaseModel):
    cert_id:int|None

class SyncOptions(BaseModel):
    start_nsu:int|None=Field(default=None,ge=0)

@app.get('/api/health')
def health():
    return {'status':'ok','service':'Codisplan NFS-e','version':'0.1.2'}

@app.get('/api/bootstrap/status')
def bootstrap_status():
    return {'needs_setup':fetchone('SELECT id FROM users LIMIT 1') is None}

@app.post('/api/bootstrap')
def bootstrap(body:Boot,request:Request):
    if request.client is None or request.client.host not in ('127.0.0.1','::1','testclient'):
        raise HTTPException(403,'Configuracao inicial somente local')
    with connect() as c:
        if c.execute('SELECT id FROM users LIMIT 1').fetchone():
            raise HTTPException(409,'Administrador ja configurado')
        c.execute('INSERT INTO users(username,password_hash) VALUES (?,?)',(body.username,hash_password(body.password)))
    audit(body.username,'bootstrap','Administrador configurado')
    return {'created':True}

@app.post('/api/auth/login')
def login(body:Login):
    row=fetchone('SELECT * FROM users WHERE username=?',(body.username,))
    if not row or not verify_password(body.password,row['password_hash']):
        raise HTTPException(401,'Credenciais invalidas')
    return {'token':create_session(row['username']),'user':row['username'],'role':row['role']}

@app.post('/api/auth/logout')
def logout(request:Request,user:str=Depends(require_admin)):
    revoke(request.headers.get('authorization','')[7:])
    return {'success':True}

@app.get('/api/companies')
def list_companies(user:str=Depends(require_admin)):
    return fetchall('''SELECT c.id,c.name,c.tax_id,c.environment,c.active,c.cert_id,t.label AS certificate_label,
        s.nsu,s.status AS sync_status,s.last_sync,s.last_message,s.query_mode
        FROM companies c LEFT JOIN certificates t ON t.id=c.cert_id
        LEFT JOIN cursors s ON s.company_id=c.id ORDER BY c.name''')

@app.post('/api/companies')
def create_company(body:CompanyIn,user:str=Depends(require_admin)):
    tax=re.sub(r'\D','',body.tax_id)
    if not valid_tax_id(tax):raise HTTPException(422,'CPF/CNPJ invalido (digito verificador)')
    with connect() as c:
        try:
            cur=c.execute('INSERT INTO companies(name,tax_id,environment,active) VALUES (?,?,?,?)',(body.name,tax,body.environment,int(body.active)))
            c.execute('INSERT INTO cursors(company_id) VALUES (?)',(cur.lastrowid,))
        except __import__('sqlite3').IntegrityError as exc:
            raise HTTPException(409,'CPF/CNPJ ja cadastrado') from exc
    audit(user,'empresa.criada',tax)
    return {'id':cur.lastrowid}

@app.put('/api/companies/{company_id}')
def update_company(company_id:int,body:CompanyIn,user:str=Depends(require_admin)):
    tax=re.sub(r'\D','',body.tax_id)
    if not valid_tax_id(tax):raise HTTPException(422,'CPF/CNPJ invalido (digito verificador)')
    with connect() as c:
        cur=c.execute('UPDATE companies SET name=?,tax_id=?,environment=?,active=? WHERE id=?',
          (body.name,tax,body.environment,int(body.active),company_id))
    if cur.rowcount<1:raise HTTPException(404,'Empresa nao encontrada')
    audit(user,'empresa.editada',str(company_id))
    return {'updated':True}

@app.post('/api/certificates')
async def upload_certificate(label:str=Form(...),password:str=Form(...),file:UploadFile=File(...),user:str=Depends(require_admin)):
    raw=await file.read(2*1024*1024+1)
    if len(raw)>2*1024*1024: raise HTTPException(413,'Arquivo PFX maior que 2 MB')
    try:
        key,cert,chain=load_key_and_certificates(raw,password.encode() if password else None)
    except Exception as exc:
        raise HTTPException(422,'Senha incorreta ou certificado PFX invalido') from exc
    if key is None or cert is None:raise HTTPException(422,'Certificado sem chave privada')
    expires=cert.not_valid_after_utc.isoformat()
    if cert.not_valid_after_utc<=datetime.now(timezone.utc):raise HTTPException(422,'Certificado expirado')
    fingerprint=cert.fingerprint(hashes.SHA256()).hex()
    with connect() as c:
        existing=c.execute('SELECT id FROM certificates WHERE fingerprint=?',(fingerprint,)).fetchone()
        if existing:raise HTTPException(409,'Certificado ja cadastrado')
        cur=c.execute('INSERT INTO certificates(label,filename,content_enc,password_enc,expires_at,fingerprint) VALUES (?,?,?,?,?,?)',
          (label,file.filename or 'certificado.pfx',encrypt(raw),encrypt(password.encode()),expires,fingerprint))
    audit(user,'certificado.importado',f'ID {cur.lastrowid}')
    return {'id':cur.lastrowid,'expires_at':expires,'fingerprint':fingerprint}

@app.get('/api/certificates')
def list_certificates(user:str=Depends(require_admin)):
    return fetchall('SELECT id,label,filename,expires_at,fingerprint,created_at FROM certificates ORDER BY label')

@app.post('/api/companies/{company_id}/certificate')
def assign_cert(company_id:int,body:AssignCert,user:str=Depends(require_admin)):
    if body.cert_id and not fetchone('SELECT id FROM certificates WHERE id=?',(body.cert_id,)):
        raise HTTPException(404,'Certificado nao localizado')
    with connect() as c:
        cur=c.execute('UPDATE companies SET cert_id=? WHERE id=?',(body.cert_id,company_id))
    if not cur.rowcount:raise HTTPException(404,'Empresa nao encontrada')
    audit(user,'certificado.vinculado',str(company_id))
    return {'updated':True}

@app.get('/api/companies/{company_id}/status')
def company_status(company_id:int,user:str=Depends(require_admin)):
    data=fetchone('SELECT * FROM cursors WHERE company_id=?',(company_id,))
    if not data:raise HTTPException(404,'Empresa nao encontrada')
    data['documents']=fetchone('SELECT COUNT(*) AS n FROM raw_documents WHERE company_id=?',(company_id,))['n']
    data['invoices']=fetchone('SELECT COUNT(*) AS n FROM invoices WHERE company_id=?',(company_id,))['n']
    return data

@app.post('/api/companies/{company_id}/sync')
def start_sync(user:str=Depends(require_admin),company_id:int=0):
    company=fetchone('SELECT * FROM companies WHERE id=?',(company_id,))
    if not company:raise HTTPException(404,'Empresa nao encontrada')
    if not company.get('cert_id'):raise HTTPException(422,'Vincule um certificado digital A1')
    result=queue_sync(company_id)
    audit(user,'sincronizacao.iniciada',str(company_id))
    return result

@app.get('/api/jobs/{job_id}')
def job_status(job_id:str,user:str=Depends(require_admin)):
    if job_id not in JOBS:raise HTTPException(404,'Tarefa nao localizada')
    return JOBS[job_id]

@app.post('/api/companies/{company_id}/adn/nsu')
def query_nsu(company_id:int,nsu:int=0,lote:bool=True,cnpjConsulta:str|None=None,cpfConsulta:str|None=None,importar:bool=False,user:str=Depends(require_admin)):
    payload=request_nsu(company_id,nsu,batch=lote,cnpj=cnpjConsulta,cpf=cpfConsulta)
    imported=0
    if importar and payload.get('StatusProcessamento')=='DOCUMENTOS_LOCALIZADOS':
        imported,_=import_lote(company_id,payload.get('LoteDFe') or [])
    audit(user,'adn.consulta.nsu',f'Empresa {company_id}; NSU {nsu}')
    return {'http_status':payload.get('http_status'),'TipoConsulta':payload.get('TipoConsulta'),
      'StatusProcessamento':payload.get('StatusProcessamento'),'TipoAmbiente':payload.get('TipoAmbiente'),
      'Erros':payload.get('Erros',[]),'Alertas':payload.get('Alertas',[]),'imported':imported,
      'LoteDFe':[{'NSU':d.get('NSU'),'ChaveAcesso':d.get('ChaveAcesso'),'TipoDocumento':d.get('TipoDocumento'),'TipoEvento':d.get('TipoEvento')} for d in (payload.get('LoteDFe') or [])]}

@app.post('/api/companies/{company_id}/adn/events/{access_key}')
def query_events(company_id:int,access_key:str,importar:bool=True,user:str=Depends(require_admin)):
    payload=request_events(company_id,access_key)
    added=0
    if importar and payload.get('StatusProcessamento')=='DOCUMENTOS_LOCALIZADOS':
        added,_=import_lote(company_id,payload.get('LoteDFe') or [])
    audit(user,'adn.consulta.eventos',f'Empresa {company_id}; chave {access_key[-6:]}')
    return {'http_status':payload.get('http_status'),'StatusProcessamento':payload.get('StatusProcessamento'),
       'imported':added,'Erros':payload.get('Erros',[]),'Alertas':payload.get('Alertas',[]),
       'LoteDFe':[{'NSU':d.get('NSU'),'TipoEvento':d.get('TipoEvento'),'TipoDocumento':d.get('TipoDocumento')} for d in (payload.get('LoteDFe') or [])]}

@app.get('/api/companies/{company_id}/documents')
def list_documents(company_id:int,limit:int=100,offset:int=0,user:str=Depends(require_admin)):
    return fetchall('SELECT id,nsu,access_key,doc_type,event_type,generated_at,sha256 FROM raw_documents WHERE company_id=? ORDER BY id DESC LIMIT ? OFFSET ?', (company_id,min(max(limit,1),500),max(offset,0)))

@app.get('/api/companies/{company_id}/documents/{document_id}/xml')
def download_xml(company_id:int,document_id:int,user:str=Depends(require_admin)):
    document=fetchone('SELECT * FROM raw_documents WHERE company_id=? AND id=?',(company_id,document_id))
    if not document:raise HTTPException(404,'Documento nao encontrado')
    content=decrypt(document['xml_enc'])
    audit(user,'xml.download',f'Empresa {company_id}; Documento {document_id}')
    return Response(content,media_type='application/xml',headers={'Content-Disposition':f'attachment; filename="nfse_{document_id}.xml"'})

@app.get('/api/companies/{company_id}/reports')
def report(company_id:int,start:str,end:str,basis:Literal['issued','competence']='issued',
    kind:Literal['mensal','competencia','iss_retido','canceladas']='mensal',
    format:Literal['json','pdf','xlsx','csv']='json',customer:str|None=None,user:str=Depends(require_admin)):
    try: summary,rows=query_report(company_id,start,end,basis,kind,customer)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    if format=='json':return as_json(summary,rows)
    generators={'pdf':(as_pdf,'application/pdf'),'xlsx':(as_xlsx,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        'csv':(as_csv,'text/csv; charset=utf-8')}
    generator,mime=generators[format]
    data=generator(summary,rows)
    audit(user,'relatorio.exportado',f'Empresa {company_id}; {kind} {start} {end}')
    return Response(data,media_type=mime,headers={'Content-Disposition':f'attachment; filename="nfse_{kind}_{start}_{end}.{format}"'})

@app.get('/api/audit')
def list_audit(user:str=Depends(require_admin)):
    return fetchall('SELECT actor,action,details,created_at FROM audit ORDER BY id DESC LIMIT 100')

@app.get('/api/info')
def info(user:str=Depends(require_admin)):
    return {'app':'Codisplan NFS-e','version':'0.1.2','data_path':str(ROOT),'host_mode':'local',
      'a3':'requer integracao PKCS#11/CSP no equipamento','official_methods':['GET /DFe/{NSU}','GET /NFSe/{ChaveAcesso}/Eventos']}

# Frontend compilado no mesmo servidor, sem dependencia de CDN.
import sys
if getattr(sys,'frozen',False):
    WEB_DIR=Path(sys._MEIPASS)/'frontend'
else:
    WEB_DIR=Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
if WEB_DIR.exists():
    @app.get('/')
    def index():return FileResponse(WEB_DIR/'index.html')
    @app.get('/logo-mark.png', include_in_schema=False)
    def logo_mark():return FileResponse(WEB_DIR/'logo-mark.png', media_type='image/png')
    @app.get('/codisplan_logo.jpg', include_in_schema=False)
    def logo_original():return FileResponse(WEB_DIR/'codisplan_logo.jpg', media_type='image/jpeg')
    app.mount('/assets',StaticFiles(directory=WEB_DIR/'assets'),name='assets')
else:
    @app.get('/')
    def no_build():return {'status':'frontend nao compilado'}
