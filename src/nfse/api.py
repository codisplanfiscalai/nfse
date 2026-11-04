"""Same-origin responsive Vue portal plus role-protected JSON REST API."""
from __future__ import annotations
import base64
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
import json
import os
from urllib.parse import urlsplit
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, Response, HTMLResponse
from starlette.staticfiles import StaticFiles
from .auth import Identity, AuthError, hash_password
from .store import Store, now
from .certificates import CertificateVault
from .adn import AdnError, validate_base_url
from .reports import REPORTS, query_report, pdf, excel, csv_bytes
from .sync import Synchronizer
from .settings import bundled, version

COOKIE='codisplan_nfse_session'
PERMISSIONS={'admin':{'dashboard','companies','certificates','sync','documents','reports','users','settings','audit'},
             'operador':{'dashboard','companies','sync','documents','reports'},
             'leitor':{'dashboard','companies','documents','reports'}}


def build_app(store:Store|None=None,*,worker:bool=True):
    store=store or Store()
    identity=Identity(store)
    vault=CertificateVault(store)
    sync=Synchronizer(store,vault) if worker else None
    app=FastAPI(title='Codisplan NFS-e',version=version(),docs_url=None,redoc_url=None)
    app.state.store=store;app.state.identity=identity;app.state.vault=vault;app.state.sync=sync

    @app.middleware('http')
    async def security_headers(request,call_next):
        if request.method not in ('GET','POST','HEAD'):
            return JSONResponse({'error':'Método não permitido.'},status_code=405)
        if request.method=='POST':
            if int(request.headers.get('content-length','0') or 0)>6*1024*1024:
                return JSONResponse({'error':'Requisição muito grande.'},status_code=413)
            origin=request.headers.get('origin')
            base=f'{request.url.scheme}://{request.headers.get("host", "")}'
            if origin and origin!=base:
                return JSONResponse({'error':'Origem não permitida.'},status_code=403)
            if request.headers.get('sec-fetch-site','') not in ('','same-origin','none'):
                return JSONResponse({'error':'Origem não permitida.'},status_code=403)
        response=await call_next(request)
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
            'Referrer-Policy':'no-referrer','X-Frame-Options':'DENY',
            'Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"})
        if request.url.scheme=='https':response.headers['Strict-Transport-Security']='max-age=31536000'
        return response

    @app.exception_handler(AuthError)
    async def auth_error(request,error):return JSONResponse({'error':str(error)},status_code=error.status)
    @app.exception_handler(AdnError)
    async def adn_error(request,error):return JSONResponse({'error':str(error),'codes':error.codes},status_code=error.status)
    @app.exception_handler(ValueError)
    async def value_error(request,error):return JSONResponse({'error':str(error)},status_code=400)

    def auth(request:Request,permission:str|None=None):
        bearer=request.headers.get('authorization','')
        api_user=None
        if bearer.startswith('Bearer '):
            api_user=identity.bearer(bearer[7:])
            user=api_user
        else:
            cookie=request.cookies.get(COOKIE,'')
            user=identity.authorize(cookie)
            if request.method=='POST':
                identity.check_csrf(cookie,request.headers.get('x-csrf-token',''))
        if permission and permission not in PERMISSIONS.get(user['role'],{}):
            raise AuthError('Perfil sem permissão para esta operação.',403)
        return user

    def respond(value):return {'data':value}

    async def payload(request):
        if request.headers.get('content-type','').split(';')[0]!='application/json':
            raise AuthError('Envie JSON.',415)
        body=await request.body()
        if len(body)>6*1024*1024:raise AuthError('Requisição excede o limite.',413)
        try:value=json.loads(body)
        except (ValueError,UnicodeError):raise ValueError('JSON inválido.') from None
        if not isinstance(value,dict):raise ValueError('Envie um objeto JSON.')
        return value

    def certificate_check(company,certificate):
        if not store.row('SELECT 1 ok FROM company_certificates WHERE company_id=? AND certificate_id=?',
                         (company,certificate)):
            raise AuthError('Certificado não autorizado para a empresa.',403)

    def adn_url():
        url=store.row('SELECT value FROM app_settings WHERE key=?',('adn_url',))
        if not url:raise ValueError('Configure primeiro a URL HTTPS oficial do ADN.')
        return validate_base_url(url['value'])

    @app.get('/health/live')
    def live():return {'status':'ok'}

    @app.get('/health/ready')
    def ready():
        store.row('SELECT count(*) AS count FROM users')
        return {'status':'ready'}

    @app.get('/api/v1/status')
    def status():return respond({'product':'Codisplan NFS-e','version':version(),
                                  'configured':identity.configured(),'types':list(REPORTS)})

    @app.post('/api/v1/setup')
    async def setup(request:Request):
        if request.client and request.client.host not in ('127.0.0.1','::1','testclient'):
            raise AuthError('Configuração inicial somente local.',403)
        d=await payload(request)
        return respond(identity.setup(d.get('name',''),d.get('email',''),d.get('password','')))

    @app.post('/api/v1/auth/login')
    async def login(request:Request):
        d=await payload(request)
        token,csrf,user=identity.login(d.get('email',''),d.get('password',''),request.client.host if request.client else 'local')
        response=JSONResponse(respond({'user':user,'csrf':csrf,'permissions':sorted(PERMISSIONS.get(user['role'],set()))}))
        response.set_cookie(COOKIE,token,max_age=28800,httponly=True,secure=request.url.scheme=='https',samesite='strict')
        response.set_cookie('codisplan_nfse_csrf',csrf,max_age=28800,httponly=False,secure=request.url.scheme=='https',samesite='strict')
        return response

    @app.get('/api/v1/auth/me')
    def me(request:Request):
        user=auth(request)
        return respond({'user':user,'csrf':request.cookies.get('codisplan_nfse_csrf',''), 'permissions':sorted(PERMISSIONS.get(user['role'],set()))})

    @app.post('/api/v1/auth/logout')
    async def logout(request:Request):
        user=auth(request);cookie=request.cookies.get(COOKIE)
        if cookie:
            from .auth import digest
            with store.transaction() as db:db.execute('DELETE FROM sessions WHERE token_hash=?',(digest(cookie),))
        response=JSONResponse(respond({'ok':True}));response.delete_cookie(COOKIE);response.delete_cookie('codisplan_nfse_csrf');return response

    @app.post('/api/v1/auth/api-token')
    async def issue_token(request:Request):
        user=auth(request,'settings');d=await payload(request)
        return respond(identity.create_token(user,d.get('name','Integração'),int(d.get('days',30))))

    @app.get('/api/v1/dashboard')
    def dashboard(request:Request):
        auth(request,'dashboard')
        return respond({'companies':store.row('SELECT COUNT(*) n FROM companies')['n'],
                        'invoices':store.row("SELECT COUNT(*) n FROM documents WHERE document_type='NFSE'")['n'],
                        'events':store.row("SELECT COUNT(*) n FROM documents WHERE document_type='EVENTO'")['n'],
                        'sync_runs':store.row('SELECT COUNT(*) n FROM sync_runs')['n'],
                        'latest':store.rows('SELECT r.id,r.status,r.started_at,r.finished_at,r.fetched,r.inserted,r.diagnostic,c.name AS company '
                                              'FROM sync_runs r JOIN companies c ON c.id=r.company_id ORDER BY r.id DESC LIMIT 8')})

    @app.get('/api/v1/companies')
    def companies(request:Request):
        auth(request,'companies')
        return respond(store.rows('SELECT id,name,identifier,active,created_at FROM companies ORDER BY name'))

    @app.post('/api/v1/companies')
    async def add_company(request:Request):
        u=auth(request,'companies');d=await payload(request)
        identifier=''.join(x for x in d.get('identifier','') if x.isdigit())
        if len(identifier) not in (11,14):raise ValueError('Informe CNPJ com 14 dígitos ou CPF com 11 dígitos.')
        if len(d.get('name','').strip())<2:raise ValueError('Informe a razão social.')
        with store.transaction() as db:
            cursor=db.execute('INSERT INTO companies(name,identifier,created_at) VALUES(?,?,?)',
                              (d['name'].strip()[:200],identifier,now()))
            id=cursor.lastrowid
        store.audit(str(u['id']),'company_add',identifier)
        return respond({'id':id})

    @app.get('/api/v1/certificates')
    def certificates(request:Request):
        auth(request,'certificates')
        return respond(store.rows('SELECT id,label,identity,subject,serial_number,expires_at FROM certificates ORDER BY id DESC'))

    @app.post('/api/v1/certificates')
    async def add_certificate(request:Request):
        u=auth(request,'certificates');d=await payload(request)
        result=vault.add(d.get('label','Certificado A1'),d.get('pfx_base64',''),d.get('password',''))
        store.audit(str(u['id']),'certificate_add',str(result['id']))
        return respond(result)

    @app.post('/api/v1/companies/{company}/certificates')
    async def link_certificate(company:int,request:Request):
        u=auth(request,'certificates');d=await payload(request)
        certificate=int(d.get('certificate_id',0))
        with store.transaction() as db:
            db.execute('INSERT OR IGNORE INTO company_certificates(company_id,certificate_id) VALUES(?,?)',(company,certificate))
        store.audit(str(u['id']),'certificate_link',f'{company}:{certificate}')
        return respond({'ok':True})

    @app.get('/api/v1/settings')
    def settings(request:Request):
        auth(request,'settings')
        r=store.row("SELECT value FROM app_settings WHERE key='adn_url'")
        return respond({'adn_url':r['value'] if r else '',
                        'note':'Use a URL HTTPS oficial do ADN; jamais uma URL de terceiros.'})

    @app.post('/api/v1/settings')
    async def set_settings(request:Request):
        u=auth(request,'settings');d=await payload(request)
        url=validate_base_url(str(d.get('adn_url','')))
        with store.transaction() as db:
            db.execute('INSERT INTO app_settings(key,value) VALUES(?,?) '
                       'ON CONFLICT(key) DO UPDATE SET value=excluded.value',('adn_url',url))
        store.audit(str(u['id']),'settings_update','adn_url')
        return respond({'ok':True})

    @app.get('/api/v1/documents')
    def documents(request:Request,company_id:int,limit:int=200,document_type:str='',status:str=''):
        auth(request,'documents')
        if not 1<=limit<=1000:raise ValueError('Limite inválido.')
        sql='SELECT id,nsu,access_key,document_type,event_type,invoice_number,issued_on,competence_on,issuer_name,recipient_name,service_cents,iss_withheld_cents,status FROM documents WHERE company_id=?'
        params=[company_id]
        if document_type:sql+=' AND document_type=?';params.append(document_type)
        if status:sql+=' AND status=?';params.append(status)
        sql+=' ORDER BY nsu DESC LIMIT ?';params.append(limit)
        return respond(store.rows(sql,params))

    @app.get('/api/v1/documents/{document_id}/xml')
    def get_xml(document_id:int,request:Request):
        auth(request,'documents')
        record=store.row('SELECT xml_content FROM documents WHERE id=?',(document_id,))
        if not record:raise AuthError('Documento não encontrado.',404)
        return Response(record['xml_content'],media_type='application/xml',headers={'Content-Disposition':f'attachment; filename="nfse-{document_id}.xml"'})

    @app.post('/api/v1/sync')
    async def start_sync(request:Request):
        u=auth(request,'sync');d=await payload(request)
        company=int(d.get('company_id',0));cert=int(d.get('certificate_id',0))
        certificate_check(company,cert)
        if sync is None:raise AuthError('Serviço de sincronização não inicializado.',503)
        cursor=d.get('initial_nsu')
        run=sync.start(company,cert,adn_url(),int(cursor) if cursor is not None else None)
        store.audit(str(u['id']),'sync_start',str(run))
        return respond({'run_id':run})

    @app.get('/api/v1/sync')
    def sync_runs(request:Request):
        auth(request,'sync')
        return respond(store.rows('SELECT id,company_id,certificate_id,started_at,finished_at,status,inserted,fetched,diagnostic FROM sync_runs ORDER BY id DESC LIMIT 100'))

    @app.post('/api/v1/adn/by-nsu')
    async def consult_nsu(request:Request):
        u=auth(request,'sync');d=await payload(request)
        company=int(d.get('company_id',0));cert=int(d.get('certificate_id',0))
        certificate_check(company,cert)
        c=store.row('SELECT identifier FROM companies WHERE id=?',(company,))
        if sync is None:raise AuthError('Serviço indisponível.',503)
        return respond(sync.preview(company,cert,adn_url(),int(d.get('nsu',0)),c['identifier'],bool(d.get('lote',True)),bool(d.get('save',False))))

    @app.post('/api/v1/adn/events')
    async def consult_events(request:Request):
        u=auth(request,'sync');d=await payload(request)
        company=int(d.get('company_id',0));cert=int(d.get('certificate_id',0))
        certificate_check(company,cert)
        if sync is None:raise AuthError('Serviço indisponível.',503)
        return respond(sync.events(company,cert,adn_url(),str(d.get('access_key','')),bool(d.get('save',False))))

    @app.get('/api/v1/reports/{kind}')
    def reports(kind:str,request:Request,company_id:int,inicio:str,fim:str,formato:str='json'):
        auth(request,'reports')
        try:r=query_report(store,company_id,kind,inicio,fim)
        except (ValueError,TypeError):raise ValueError('Parâmetros do relatório inválidos.') from None
        if formato=='json':
            # XML raw bytes are not returned by the JSON report.
            for row in r['rows']:
                row.pop('xml_content',None)
            return respond(r)
        if formato=='pdf':content,media,extension=pdf(r),'application/pdf','pdf'
        elif formato=='xlsx':content,media,extension=excel(r),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','xlsx'
        elif formato=='csv':content,media,extension=csv_bytes(r),'text/csv; charset=utf-8','csv'
        else:raise ValueError('Formato deve ser json, pdf, xlsx ou csv.')
        return Response(content,media_type=media,headers={'Content-Disposition':f'attachment; filename="nfse-{kind}-{inicio}-{fim}.{extension}"'})

    @app.get('/api/v1/audit')
    def audit(request:Request):
        auth(request,'audit')
        return respond(store.rows('SELECT * FROM audit_log ORDER BY id DESC LIMIT 200'))

    @app.get('/api/v1/users')
    def users(request:Request):
        auth(request,'users')
        return respond(store.rows('SELECT id,name,email,role,active,created_at FROM users ORDER BY id'))

    @app.post('/api/v1/users')
    async def add_user(request:Request):
        u=auth(request,'users');d=await payload(request)
        role=d.get('role','leitor')
        if role not in PERMISSIONS:raise ValueError('Perfil inválido.')
        with store.transaction() as db:
            cur=db.execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',
                           (str(d.get('name',''))[:200],str(d.get('email','')).lower()[:200],hash_password(d.get('password','')),role,now()))
        store.audit(str(u['id']),'user_add',str(cur.lastrowid))
        return respond({'id':cur.lastrowid})

    assets=bundled('src/nfse/portal')
    if assets.exists():
        @app.get('/')
        def home():return FileResponse(assets/'index.html',media_type='text/html')
        app.mount('/static',StaticFiles(directory=assets),name='static')
    return app
