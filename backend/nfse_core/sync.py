from __future__ import annotations
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4
from .adn import AdnError, request_nsu, request_events
from .db import fetchone, fetchall, connect
from .storage import import_lote
from .settings import MAX_BATCHES

_EXECUTOR = ThreadPoolExecutor(max_workers=3, thread_name_prefix='nfse-sync')
_LOCK=threading.RLock()
_RUNNING:set[int]=set()
JOBS:dict[str,dict]={}


def _update_cursor(company_id, **fields):
    if not fields:return
    sets=','.join(k+'=?' for k in fields)
    with connect() as c:
        c.execute('INSERT OR IGNORE INTO cursors(company_id) VALUES (?)',(company_id,))
        c.execute('UPDATE cursors SET '+sets+' WHERE company_id=?',[*fields.values(),company_id])


def sync_company(company_id:int, job_id:str|None=None):
    try:
        current=fetchone('SELECT * FROM cursors WHERE company_id=?',(company_id,)) or {'nsu':0}
        nsu=int(current['nsu'])
        company=fetchone('SELECT * FROM companies WHERE id=?',(company_id,))
        if not company or not company['active']: raise ValueError('Empresa inativa ou inexistente')
        _update_cursor(company_id,status='sincronizando',last_message='')
        n=0;last_mode=''
        for _ in range(MAX_BATCHES):
            answer=request_nsu(company_id,nsu,batch=True,cnpj=company['tax_id'] if len(company['tax_id'])==14 else None,cpf=company['tax_id'] if len(company['tax_id'])==11 else None)
            last_mode=answer.get('TipoConsulta','')
            status=answer.get('StatusProcessamento')
            if answer['http_status']==404 and status=='NENHUM_DOCUMENTO_LOCALIZADO':break
            if status!='DOCUMENTOS_LOCALIZADOS':
                raise AdnError(502,'Status ADN inesperado: '+str(status),answer.get('Erros'))
            docs=answer.get('LoteDFe') or []
            if not docs:break
            next_nsu=max((int(x.get('NSU') or 0) for x in docs),default=nsu)
            if next_nsu<=nsu: raise AdnError(502,'ADN retornou lote sem avancar NSU')
            imported,_=import_lote(company_id,docs)
            nsu=next_nsu;n+=imported
            _update_cursor(company_id,nsu=nsu,last_sync=datetime.now(timezone.utc).isoformat(),status='sincronizando',query_mode=last_mode)
        _update_cursor(company_id,nsu=nsu,last_sync=datetime.now(timezone.utc).isoformat(),status='ok',last_message=f'Importados {n} novos documentos',query_mode=last_mode)
        if job_id:JOBS[job_id].update(state='ok',imported=n,nsu=nsu)
        return {'imported':n,'nsu':nsu}
    except Exception as exc:
        _update_cursor(company_id,status='erro',last_message=str(exc)[:250])
        if job_id:JOBS[job_id].update(state='erro',error=str(exc)[:250])
        raise
    finally:
        with _LOCK:_RUNNING.discard(company_id)


def queue_sync(company_id:int):
    with _LOCK:
        if company_id in _RUNNING: return {'scheduled':False,'detail':'Sincronizacao ja em execucao'}
        _RUNNING.add(company_id)
        job_id=str(uuid4())
        JOBS[job_id]={'id':job_id,'company_id':company_id,'state':'executando','imported':0}
    _EXECUTOR.submit(_worker,company_id,job_id)
    return {'scheduled':True,'job_id':job_id}


def _worker(company_id,job_id):
    try:sync_company(company_id,job_id)
    except Exception:pass # status sanitizado registrado no banco e API


class Scheduler:
    def __init__(self, every_seconds=900):
        self.every_seconds=every_seconds
        self.stop_event=threading.Event()
        self.thread=None

    def start(self):
        if self.thread and self.thread.is_alive():return
        self.stop_event.clear()
        self.thread=threading.Thread(target=self._run,name='nfse-scheduler',daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stop_event.wait(self.every_seconds):
            for company in fetchall('SELECT id FROM companies WHERE active=1 AND cert_id IS NOT NULL'):
                queue_sync(company['id'])

    def stop(self):
        self.stop_event.set()
        if self.thread:self.thread.join(timeout=3)
