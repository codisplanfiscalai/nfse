"""Authorized ADN distribution with transactional bookmarks and strict tenant isolation."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import threading
from .adn import AdnClient, decode_xml
from .certificates import CertificateVault
from .store import Store, now
from .xml_documents import normalize


class Synchronizer:
    def __init__(self, store:Store, vault:CertificateVault):
        self.store,self.vault=store,vault
        self.lock=threading.Lock()
        self.active=set()
        self.executor=ThreadPoolExecutor(max_workers=2,thread_name_prefix='nfse-sync')

    def start(self,company:int,cert:int,url:str,initial_nsu:int|None=None):
        key=(company,cert)
        with self.lock:
            if key in self.active:
                raise ValueError('Sincronização já em execução para empresa/certificado.')
            self.active.add(key)
        with self.store.transaction() as db:
            row=db.execute('INSERT INTO sync_runs(company_id,certificate_id,started_at,status) VALUES(?,?,?,?)',
                           (company,cert,now(),'EXECUTANDO'))
            run_id=row.lastrowid
        self.executor.submit(self._run,run_id,company,cert,url,initial_nsu)
        return run_id

    def _run(self,run_id,company,cert,url,initial_nsu):
        inserted_total=0; fetched_total=0; status='CONCLUIDA'; diagnosis=''
        try:
            company_row=self.store.row('SELECT * FROM companies WHERE id=? AND active=1',(company,))
            linked=self.store.row('SELECT 1 as ok FROM company_certificates WHERE company_id=? AND certificate_id=?',(company,cert))
            if not company_row or not linked:raise ValueError('Empresa/certificado sem vínculo autorizado.')
            prior=self.store.row('SELECT last_nsu FROM sync_cursors WHERE company_id=? AND certificate_id=?',(company,cert))
            cursor=prior['last_nsu'] if prior else (int(initial_nsu) if initial_nsu is not None else 0)
            with self.vault.client_context(cert) as context:
                client=AdnClient(url,context)
                for _ in range(100):
                    result=client.by_nsu(cursor,cnpj=company_row['identifier'] if len(company_row['identifier'])==14 else None,
                                         cpf=company_row['identifier'] if len(company_row['identifier'])==11 else None,lote=True)
                    if result['StatusProcessamento']=='NENHUM_DOCUMENTO_LOCALIZADO':break
                    docs=[]
                    for item in result.get('LoteDFe') or []:
                        xml=decode_xml(item['ArquivoXml'])
                        docs.append(normalize(item,xml))
                    if not docs:break
                    if min(x['nsu'] for x in docs)<=cursor:
                        raise ValueError('ADN retornou NSU igual ou inferior ao cursor; sincronização interrompida.')
                    inserted,cursor=self.store.apply_documents(company,cert,docs)
                    inserted_total+=inserted;fetched_total+=len(docs)
                    if len(docs)<1:break
                else:
                    status='PARCIAL';diagnosis='Limite de 100 lotes atingido; retome a sincronização.'
        except Exception as error:
            status='ERRO'
            diagnosis=str(error)[:900]
        finally:
            with self.store.transaction() as db:
                db.execute('UPDATE sync_runs SET finished_at=?,status=?,inserted=?,fetched=?,diagnostic=? WHERE id=?',
                           (now(),status,inserted_total,fetched_total,diagnosis,run_id))
            with self.lock:self.active.discard((company,cert))

    def preview(self,company:int,cert:int,url:str,nsu:int,identifier:str='',lote:bool=True,save:bool=False):
        with self.vault.client_context(cert) as context:
            client=AdnClient(url,context)
            kwargs={'lote':lote}
            if len(identifier)==14:kwargs['cnpj']=identifier
            elif len(identifier)==11:kwargs['cpf']=identifier
            result=client.by_nsu(nsu,**kwargs)
        inserted=0
        if save:
            records=[normalize(x,decode_xml(x['ArquivoXml'])) for x in result.get('LoteDFe') or []]
            if records:inserted,_=self.store.apply_documents(company,cert,records,advance=False)
        return {k:v for k,v in result.items() if k!='LoteDFe'} | {
            'salvos':inserted,'documentos':[{'NSU':x.get('NSU'),'ChaveAcesso':x.get('ChaveAcesso'),
                           'TipoDocumento':x.get('TipoDocumento'),'TipoEvento':x.get('TipoEvento')}
                          for x in result.get('LoteDFe') or []]}

    def events(self,company:int,cert:int,url:str,key:str,save:bool=False):
        with self.vault.client_context(cert) as context:
            client=AdnClient(url,context)
            result=client.events(key)
        inserted=0
        if save:
            records=[normalize(x,decode_xml(x['ArquivoXml'])) for x in result.get('LoteDFe') or []]
            if records:inserted,_=self.store.apply_documents(company,cert,records,advance=False)
        return {'status':result['StatusProcessamento'],'salvos':inserted,'documentos':[
            {'NSU':x.get('NSU'),'ChaveAcesso':x.get('ChaveAcesso'),'TipoDocumento':x.get('TipoDocumento'),
             'TipoEvento':x.get('TipoEvento')} for x in result.get('LoteDFe') or []]}
