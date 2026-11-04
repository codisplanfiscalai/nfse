from __future__ import annotations
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from defusedxml import ElementTree as ET


def child(node, *path):
    for part in path:
        if node is None: return None
        node = next((c for c in node if c.tag.rsplit('}', 1)[-1] == part), None)
    return node


def first(node, *paths):
    for path in paths:
        n = child(node, *path)
        if n is not None and n.text and n.text.strip():
            return n.text.strip()
    return None


def tax_id(node):
    return first(node, ('CNPJ',), ('CPF',))


def date_only(value):
    if not value: return None
    value = value[:10]
    try: return datetime.strptime(value, '%Y-%m-%d').date().isoformat()
    except ValueError: return None


def cents(value):
    if not value: return 0
    try:
        return int((Decimal(value) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except InvalidOperation:
        return 0


def parse_nfse(xml: bytes, access_key: str):
    if len(xml) > 15 * 1024 * 1024 or b'<!DOCTYPE' in xml.upper():
        raise ValueError('XML inseguro ou acima do limite')
    root = ET.fromstring(xml)
    nfse = root if root.tag.rsplit('}', 1)[-1] == 'NFSe' else child(root, 'NFSe')
    if nfse is None:
        raise ValueError('Documento nao corresponde a NFSe')
    inf = child(nfse, 'infNFSe')
    if inf is None: raise ValueError('infNFSe nao encontrado')
    inf_dps = child(inf, 'DPS', 'infDPS')
    emit = child(inf, 'emit')
    prest = child(inf_dps, 'prest')
    toma = child(inf_dps, 'toma')
    serv = child(inf_dps, 'serv', 'cServ')
    val = child(inf, 'valores')
    val_dps = child(inf_dps, 'valores')
    trib_fed = child(val_dps, 'trib', 'tribFed')
    trib_mun = child(val_dps, 'trib', 'tribMun')
    identifier = inf.attrib.get('Id', '')
    m = re.match(r'^NFS(\d{50})$', identifier)
    if m and access_key and m.group(1) != access_key:
        raise ValueError('Chave informada difere da chave no XML')
    key = (m.group(1) if m else access_key)
    if not key or not re.fullmatch(r'\d{50}', key):
        raise ValueError('Chave invalida no XML da NFSe')
    code = first(trib_mun, ('tpRetISSQN',))
    # A codificacao vigente utiliza 1 (nao retido), 2 (retido pelo tomador) e 3 (retido pelo intermediario).
    retained = code in ('2','3')
    return {
        'access_key': key, 'number': first(inf, ('nNFSe',)),
        'issued_at': date_only(first(inf_dps, ('dhEmi',)) or first(inf, ('dhProc',))),
        'competence': date_only(first(inf_dps, ('dCompet',))),
        'provider_id': tax_id(prest) or tax_id(emit),
        'customer_id': tax_id(toma), 'customer_name': first(toma, ('xNome',)),
        'service_code': first(serv, ('cTribNac',), ('cTribMun',)),
        'service_desc': first(serv, ('xDescServ',)),
        'amount_cents': cents(first(val_dps, ('vServPrest','vServ'), ('vServ',)) or first(val, ('vServ',))),
        'net_cents': cents(first(val, ('vLiq',))),
        'iss_cents': cents(first(val, ('vISSQN',))),
        'irrf_cents': cents(first(trib_fed, ('vRetIRRF',))),
        'inss_cents': cents(first(trib_fed, ('vRetCP',))),
        'pcc_cents': cents(first(trib_fed, ('vRetCSLL',))),
        'iss_retained': int(retained), 'iss_retention_code': code,
        'substitute_key': first(inf_dps, ('subst','chSubstda')),
        'status': 'autorizada',
    }


CANCEL_EVENTS = {'CANCELAMENTO','CANCELAMENTO_DEFERIDO_ANALISE_FISCAL','CANCELAMENTO_POR_OFICIO'}
SUBSTITUTE_EVENTS = {'CANCELAMENTO_POR_SUBSTITUICAO'}
EVENT_CODE_MAP = {'e101101':'CANCELAMENTO'}


def normalize_event(value):
    return EVENT_CODE_MAP.get(value, value or 'DESCONHECIDO')
