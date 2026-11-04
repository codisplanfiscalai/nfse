from __future__ import annotations
import hashlib
import re
from .db import transaction, fetchone
from .crypto import encrypt
from .xml_normalizer import parse_nfse, normalize_event, CANCEL_EVENTS, SUBSTITUTE_EVENTS
from .adn import decode_xml


def _reconcile(c, company_id: int, access_key: str):
    events = [e['event_type'] for e in c.execute('SELECT event_type FROM events WHERE company_id=? AND access_key=?',(company_id,access_key))]
    status = 'substituida' if any(e in SUBSTITUTE_EVENTS for e in events) else 'cancelada' if any(e in CANCEL_EVENTS for e in events) else 'autorizada'
    c.execute('UPDATE invoices SET status=? WHERE company_id=? AND access_key=?', (status, company_id, access_key))


def import_one(company_id: int, entry: dict) -> bool:
    """Grava atomica e idempotentemente, preservando XMLs de eventos e outros tipos."""
    if not isinstance(entry, dict): raise ValueError('DFe invalido')
    doc_type = str(entry.get('TipoDocumento') or 'NENHUM').upper()
    key = str(entry.get('ChaveAcesso') or '')
    nsu = entry.get('NSU')
    if nsu is not None and (not isinstance(nsu, int) or nsu < 0): raise ValueError('NSU invalido')
    if not re.fullmatch(r'\d{50}', key): raise ValueError('Chave de acesso invalida')
    xml = decode_xml(entry['ArquivoXml'])
    digest = hashlib.sha256(xml).hexdigest()
    event_type = normalize_event(str(entry.get('TipoEvento') or '')) if doc_type == 'EVENTO' else None
    normalized = parse_nfse(xml, key) if doc_type == 'NFSE' else None
    with transaction() as c:
        existing = c.execute('SELECT id FROM raw_documents WHERE company_id=? AND doc_type=? AND sha256=?', (company_id, doc_type, digest)).fetchone()
        if existing: return False
        c.execute('INSERT INTO raw_documents(company_id,nsu,access_key,doc_type,event_type,xml_enc,sha256,generated_at) VALUES (?,?,?,?,?,?,?,?)',
                  (company_id,nsu,key,doc_type,event_type,encrypt(xml),digest,entry.get('DataHoraGeracao')))
        if normalized:
            cols=list(normalized)
            c.execute(f'INSERT INTO invoices(company_id,{",".join(cols)}) VALUES ({",".join(["?"]*(len(cols)+1))}) ON CONFLICT(company_id,access_key) DO UPDATE SET ' + ','.join(f'{k}=excluded.{k}' for k in cols if k != 'access_key' and k != 'status'),
                      [company_id]+[normalized[k] for k in cols])
            _reconcile(c, company_id, key)
            if normalized['substitute_key']:
                c.execute('UPDATE invoices SET status=? WHERE company_id=? AND access_key=?', ('substituida',company_id, normalized['substitute_key']))
        elif doc_type == 'EVENTO':
            c.execute('INSERT OR IGNORE INTO events(company_id,access_key,event_type,event_nsu,sha256) VALUES (?,?,?,?,?)', (company_id,key,event_type,nsu,digest))
            _reconcile(c, company_id, key)
    return True


def import_lote(company_id: int, lote: list) -> tuple[int, int | None]:
    count=0
    max_nsu=None
    for item in lote:
        changed=import_one(company_id,item)
        count+=int(changed)
        if item.get('NSU') is not None:
            max_nsu=max(max_nsu or 0, item['NSU'])
    return count,max_nsu
