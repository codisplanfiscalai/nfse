"""Namespace-safe XML normalizer for NFSe, DPS and events; no external entities."""
from __future__ import annotations
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import re
from defusedxml import ElementTree as DET

EVENT_TYPES={
 'CANCELAMENTO','SOLICITACAO_CANCELAMENTO_ANALISE_FISCAL','CANCELAMENTO_POR_SUBSTITUICAO',
 'CANCELAMENTO_DEFERIDO_ANALISE_FISCAL','CANCELAMENTO_INDEFERIDO_ANALISE_FISCAL',
 'CONFIRMACAO_PRESTADOR','REJEICAO_PRESTADOR','CONFIRMACAO_TOMADOR','REJEICAO_TOMADOR',
 'CONFIRMACAO_INTERMEDIARIO','REJEICAO_INTERMEDIARIO','CONFIRMACAO_TACITA',
 'ANULACAO_REJEICAO','CANCELAMENTO_POR_OFICIO','BLOQUEIO_POR_OFICIO','DESBLOQUEIO_POR_OFICIO',
 'TRIBUTOS_NFSE_RECOLHIDOS','INCLUSAO_NFSE_DAN'
}
DOCUMENT_TYPES={'DPS','PEDIDO_REGISTRO_EVENTO','NFSE','EVENTO','CNC','NENHUM'}


def local(tag):return tag.rsplit('}',1)[-1]


def find(element,path):
    obj=element
    for part in path.split('/'):
        if obj is None:return None
        obj=next((x for x in obj if local(x.tag)==part),None)
    return obj


def find_any(element,*paths):
    for path in paths:
        node=find(element,path)
        if node is not None:
            value=(node.text or '').strip()
            if value:return value
    return ''


def cents(element,*paths):
    value=find_any(element,*paths)
    if not value:return 0
    try:
        decimal=Decimal(value)
        if not decimal.is_finite() or decimal<0 or decimal>Decimal('99999999999999'):
            raise ValueError('Valor monetário fora dos limites.')
        return int((decimal*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    except (ValueError,InvalidOperation):
        raise ValueError('Valor monetário inválido em XML: '+value[:25]) from None


def normalize(item:dict,xml:bytes):
    kind=str(item.get('TipoDocumento') or '').upper()
    if kind not in DOCUMENT_TYPES:raise ValueError('TipoDocumento desconhecido: '+kind)
    key=str(item.get('ChaveAcesso') or '').strip()
    if not key:raise ValueError('ChaveAcesso não informada.')
    nsu=int(item['NSU'])
    root=DET.fromstring(xml)
    info=find(root,'infNFSe')
    if info is None and local(root.tag)=='infNFSe':info=root
    dps=find(info,'DPS/infDPS') if info is not None else None
    if dps is None:dps=find(root,'infDPS')
    if dps is None and info is not None:
        dps=find(info,'DPS')
    if dps is None:dps=root
    src=info if info is not None else root
    emit=find(src,'emit')
    prest=find(dps,'prest')
    toma=find(dps,'toma')
    base=emit if emit is not None else prest
    # Extract from known paths only: never search globally for unrelated vServ fields.
    identity=find_any(base,'CNPJ','CPF') if base is not None else ''
    name=find_any(base,'xNome') if base is not None else ''
    recip=find_any(toma,'CNPJ','CPF') if toma is not None else ''
    recipient_name=find_any(toma,'xNome') if toma is not None else ''
    # NFS-e issuance is its authorization timestamp; DPS creation is only a fallback.
    issued=find_any(src,'dhProc','dhEmi') or find_any(dps,'dhEmi')
    competence=find_any(dps,'dCompet')
    service=cents(dps,'valores/vServPrest/vServ','valores/vServ')
    # Difference between ISS calculated and ISS retained: prefer explicit retained value.
    iss=cents(src,'valores/vISSQN','valores/vISS')
    tp_ret=find_any(dps,'valores/trib/tribMun/tpRetISSQN')
    iss_ret=cents(src,'valores/vISSRet','valores/vISSQNRet')
    if not iss_ret and tp_ret in ('1','2'):
        # Some layouts indicate retention with tpRetISSQN; 1 indicates no withholding in some versions.
        # Do not manufacture retained amount from total ISS when the XML omits vISSRet.
        iss_ret=0
    irrf=cents(dps,'valores/trib/tribFed/vRetIRRF')
    inss=cents(dps,'valores/trib/tribFed/vRetCP')
    pcc=cents(dps,'valores/trib/tribFed/vRetCSLL')
    net=cents(src,'valores/vLiq')
    event_type=str(item.get('TipoEvento') or '').upper() or None
    # National NFS-e event code e101101 identifies cancellation in XML responses.
    # Preserve every other unknown numeric code without inferring its fiscal effects.
    if kind=='EVENTO' and event_type=='E101101':
        event_type='CANCELAMENTO'
    return {
        'nsu':nsu,'access_key':key,'document_type':kind,
        'event_type':event_type,
        'generated_at':str(item.get('DataHoraGeracao') or ''),
        'issuer_identifier':identity,'issuer_name':name,
        'recipient_identifier':recip,'recipient_name':recipient_name,
        'invoice_number':find_any(src,'nNFSe','nDFSe'),
        'issued_on':issued[:10] if issued else None,
        'competence_on':competence[:10] if competence else (issued[:10] if issued else None),
        'service_code':find_any(dps,'serv/cServ/cTribNac','serv/cServ/cTribMun'),
        'service_description':find_any(dps,'serv/cServ/xDescServ'),
        'service_cents':service,'net_cents':net,'iss_cents':iss,
        'iss_withheld_cents':iss_ret,'irrf_cents':irrf,'inss_cents':inss,
        'pcc_cents':pcc,'xml_sha256':hashlib.sha256(xml).hexdigest(),
        'xml_content':xml,
    }
