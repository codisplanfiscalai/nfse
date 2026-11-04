"""Strict contract for ADN Contribuinte Swagger endpoints."""
from __future__ import annotations
import base64
import gzip
import io
import re
import ssl
import httpx
from urllib.parse import urlsplit

MAX_RESPONSE=18*1024*1024
MAX_XML=6*1024*1024


class AdnError(Exception):
    def __init__(self, message, status=502, codes=None):
        super().__init__(message)
        self.status=status
        self.codes=codes or []


def validate_base_url(url: str) -> str:
    url=(url or '').strip().rstrip('/')
    parsed=urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Informe URL HTTPS oficial do ADN, sem autenticação ou parâmetros.')
    if parsed.port not in (None,443):
        raise ValueError('A API ADN deve utilizar a porta HTTPS padrão.')
    if not (parsed.hostname=='nfse.gov.br' or parsed.hostname.endswith('.nfse.gov.br')):
        raise ValueError('Somente domínios oficiais nfse.gov.br são permitidos.')
    return url


def decode_xml(blob: str) -> bytes:
    if not isinstance(blob,str) or len(blob)>12*1024*1024:
        raise AdnError('ArquivoXml excede o limite de tamanho.')
    try:
        compressed=base64.b64decode(blob,validate=True)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as file:
            content=file.read(MAX_XML+1)
        if len(content)>MAX_XML:
            raise AdnError('XML descompactado excede o limite de tamanho.')
        if not content.lstrip().startswith(b'<'):
            raise AdnError('XML descompactado inválido.')
        return content
    except (OSError, ValueError) as error:
        raise AdnError('ArquivoXml inválido (base64/gzip).') from error


class AdnClient:
    def __init__(self, base_url: str, ssl_context: ssl.SSLContext, transport=None):
        self.base_url=validate_base_url(base_url)
        self.ssl_context=ssl_context
        self.transport=transport

    def request(self, path: str, params=None):
        if not path.startswith('/') or '//' in path or '?' in path:
            raise ValueError('Caminho ADN inválido.')
        with httpx.Client(verify=self.ssl_context,transport=self.transport,
                          timeout=httpx.Timeout(30,connect=10),follow_redirects=False,
                          trust_env=False,headers={'Accept':'application/json'}) as client:
            response=client.get(self.base_url+path,params=params)
        if len(response.content)>MAX_RESPONSE:
            raise AdnError('Resposta ADN excede o limite.')
        try: data=response.json()
        except ValueError as e:raise AdnError('ADN retornou resposta não JSON.',response.status_code) from e
        if not isinstance(data,dict):
            raise AdnError('Formato de resposta ADN inválido.')
        codes=[{'code':str(x.get('Codigo','')),'description':str(x.get('Descricao',''))}
               for x in (data.get('Erros') or []) if isinstance(x,dict)]
        if response.status_code==404 and data.get('StatusProcessamento')=='NENHUM_DOCUMENTO_LOCALIZADO':
            if any(x['code'] in {'E2220','E2230','E2240'} for x in codes):
                return {'StatusProcessamento':'NENHUM_DOCUMENTO_LOCALIZADO','LoteDFe':[],
                        'TipoConsulta':data.get('TipoConsulta'),'Erros':codes}
        if response.status_code>=400 or data.get('StatusProcessamento')=='REJEICAO':
            raise AdnError('ADN rejeitou a consulta: '+('; '.join(x['code']+' '+x['description'] for x in codes) or 'HTTP '+str(response.status_code)),response.status_code,codes)
        if data.get('StatusProcessamento')!='DOCUMENTOS_LOCALIZADOS':
            raise AdnError('StatusProcessamento desconhecido: '+str(data.get('StatusProcessamento')))
        if not isinstance(data.get('LoteDFe'),list):
            raise AdnError('LoteDFe ausente ou inválido.')
        return data

    def by_nsu(self, nsu:int, *, cnpj:str|None=None, cpf:str|None=None, lote:bool=True):
        if int(nsu)<0:raise ValueError('NSU não pode ser negativo.')
        if cnpj and cpf:raise ValueError('cnpjConsulta e cpfConsulta são mutuamente exclusivos.')
        if cnpj and not re.fullmatch(r'\d{14}',cnpj):raise ValueError('cnpjConsulta exige 14 dígitos.')
        if cpf and not re.fullmatch(r'\d{11}',cpf):raise ValueError('cpfConsulta exige 11 dígitos.')
        params={'lote':str(bool(lote)).lower()}
        if cnpj:params['cnpjConsulta']=cnpj
        if cpf:params['cpfConsulta']=cpf
        return self.request(f'/DFe/{int(nsu)}',params)

    def events(self, access_key: str):
        if not re.fullmatch(r'[A-Za-z0-9]{30,80}',access_key):
            raise ValueError('Chave de acesso inválida.')
        return self.request(f'/NFSe/{access_key}/Eventos')
