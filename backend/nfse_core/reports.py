from __future__ import annotations
from collections import defaultdict
from datetime import date
from decimal import Decimal
from io import BytesIO, StringIO
import csv
import html
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle
from .db import fetchone, fetchall

VALUE_FIELDS = ['amount_cents','net_cents','iss_cents','irrf_cents','inss_cents','pcc_cents']
COLUMNS = [
 ('customer_id','Tomador CPF/CNPJ'), ('customer_name','Razao social / tomador'),
 ('provider_id','Emitente CPF/CNPJ'), ('number','Numero NFS-e'),
 ('amount_cents','Servicos (R$)'), ('net_cents','Liquido (R$)'),
 ('iss_cents','ISS (R$)'), ('iss_retention_code','Retencao ISS'),
 ('irrf_cents','IRRF (R$)'), ('inss_cents','INSS (R$)'),
 ('pcc_cents','PIS/COFINS/CSLL retidos (R$)'),
 ('issued_at','Emissao'), ('competence','Competencia'),
 ('service_code','Codigo servico'), ('service_desc','Descricao do servico'),
 ('status','Situacao'), ('access_key','Chave de acesso'),
]


def money(cents: int | None) -> str:
    n = int(cents or 0)
    return ('-' if n < 0 else '') + f'{abs(n)//100:,}'.replace(',', '.') + ',' + f'{abs(n)%100:02d}'


def query_report(company_id:int, start:str, end:str, basis:str='issued', kind:str='mensal', customer:str|None=None):
    company = fetchone('SELECT id,name,tax_id FROM companies WHERE id=?',(company_id,))
    if not company: raise ValueError('Empresa nao encontrada')
    try:
        if date.fromisoformat(start) > date.fromisoformat(end): raise ValueError('Data inicial posterior a final')
    except (TypeError,ValueError) as exc:
        raise ValueError('Periodo invalido: informe YYYY-MM-DD, inicio <= fim') from exc
    if basis not in ('issued','competence'): raise ValueError('Base de data invalida')
    if kind not in ('mensal','competencia','iss_retido','canceladas'): raise ValueError('Tipo de relatorio invalido')
    datecol = 'issued_at' if basis == 'issued' else 'competence'
    cond = [f'{datecol} BETWEEN ? AND ?', 'provider_id=?']
    args=[start,end,company['tax_id']]
    if kind == 'iss_retido':
        cond.extend(['iss_retained=1', "status='autorizada'"])
    if kind == 'canceladas': cond.append("status IN ('cancelada','substituida')")
    if kind in ('mensal','competencia'): cond.append("status='autorizada'")
    if customer:
        cond.append('customer_id=?'); args.append(''.join(c for c in customer if c.isdigit()))
    rows=fetchall('SELECT * FROM invoices WHERE company_id=? AND '+ ' AND '.join(cond) +' ORDER BY '+datecol+',number', (company_id,*args))
    totals={field:sum(int(x.get(field) or 0) for x in rows) for field in VALUE_FIELDS}
    summary={ 'company':company, 'start':start, 'end':end, 'basis':basis, 'kind':kind,
      'count':len(rows), 'totals':{field:money(val) for field,val in totals.items()}}
    return summary, rows


def _title(kind: str):
    return {'mensal':'NFS-e Emitidas - Por Emissao', 'competencia':'NFS-e Emitidas - Por Competencia',
      'iss_retido':'NFS-e Emitidas - ISS Retido', 'canceladas':'NFS-e Emitidas - Canceladas e Substituidas'}[kind]


def _cell(row,key):
    value=row.get(key)
    if key in VALUE_FIELDS: return money(value)
    if key=='iss_retention_code': return 'Sim' if row.get('iss_retained') else 'Nao'
    return str(value if value is not None else '')


def as_json(summary,rows):
    return {'summary':summary, 'columns':[{'field':a,'label':b} for a,b in COLUMNS],
            'items':[{key:(_cell(r,key) if key in VALUE_FIELDS else r.get(key)) for key,_ in COLUMNS} for r in rows]}


def as_csv(summary, rows) -> bytes:
    out=StringIO()
    writer=csv.writer(out, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow([_title(summary['kind'])])
    writer.writerow([summary['company']['name'],summary['company']['tax_id'],summary['start'],summary['end']])
    writer.writerow([h for _,h in COLUMNS])
    for row in rows:
        writer.writerow([_cell(row,k) for k,_ in COLUMNS])
    writer.writerow(['TOTAL',str(len(rows))]+[summary['totals'].get(x,'') for x in VALUE_FIELDS])
    return ('\ufeff'+out.getvalue()).encode('utf-8')


def as_xlsx(summary,rows) -> bytes:
    wb=Workbook()
    sheet=wb.active; sheet.title='Relatorio'
    sheet.append([_title(summary['kind'])])
    sheet.append(['Empresa',summary['company']['name'],'CNPJ',summary['company']['tax_id']])
    sheet.append(['Periodo',summary['start'],summary['end'],'Criterio',summary['basis']])
    sheet.append([]); sheet.append([h for _,h in COLUMNS])
    sheet.freeze_panes='C6'; sheet.auto_filter.ref=f'A5:Q{max(5,5+len(rows))}'
    for row in rows:
        sheet.append([int(row.get(k) or 0)/100 if k in VALUE_FIELDS else _cell(row,k) for k,_ in COLUMNS])
    for r in sheet.iter_rows(min_row=6):
        for col_idx in (5,6,7,9,10,11):
            r[col_idx-1].number_format='#,##0.00;[Red]-#,##0.00'
    last=6+len(rows)
    sheet.cell(last,1,'TOTAL')
    sheet.cell(last,2,len(rows))
    for col,key in ((5,'amount_cents'),(6,'net_cents'),(7,'iss_cents'),(9,'irrf_cents'),(10,'inss_cents'),(11,'pcc_cents')):
        sheet.cell(last,col,f'=SUM({get_column_letter(col)}6:{get_column_letter(col)}{last-1})').number_format='#,##0.00'
    for cell in sheet[5]:
        cell.fill=PatternFill('solid',fgColor='D5DBE3'); cell.font=Font(bold=True)
        cell.alignment=Alignment(wrap_text=True,vertical='center')
    sheet.row_dimensions[5].height=32
    for i,(key,label) in enumerate(COLUMNS,1):
        width=36 if key in ('customer_name','service_desc') else 52 if key=='access_key' else 24 if key.endswith('_cents') else 20
        sheet.column_dimensions[get_column_letter(i)].width=width
    by_customer=wb.create_sheet('Por Tomador'); by_customer.append(['CNPJ CPF','Tomador','Notas','Servicos R$','ISS R$','PCC R$'])
    grouped={}
    for r in rows:
        key=(r.get('customer_id'),r.get('customer_name'))
        x=grouped.setdefault(key,{'n':0,'a':0,'iss':0,'pcc':0})
        x['n']+=1;x['a']+=r['amount_cents'];x['iss']+=r['iss_cents'];x['pcc']+=r['pcc_cents']
    for (doc,name),a in sorted(grouped.items(),key=lambda item: str(item[0])):
        by_customer.append([doc,name,a['n'],a['a']/100,a['iss']/100,a['pcc']/100])
    for col in 'ABCDEF': by_customer.column_dimensions[col].width=25 if col!='B' else 45
    by_service=wb.create_sheet('Por Servico');by_service.append(['Codigo','Descricao','Notas','Servicos R$'])
    g={}
    for r in rows:
        key=(r.get('service_code'),r.get('service_desc'))
        x=g.setdefault(key,[0,0]);x[0]+=1;x[1]+=r['amount_cents']
    for (code,desc),(n,value) in sorted(g.items(),key=lambda item: str(item[0])):
        by_service.append([code,desc,n,value/100])
    by_service.column_dimensions['B'].width=65
    by_month=wb.create_sheet('Por Competencia');by_month.append(['Competencia','Notas','Servicos R$','ISS R$'])
    months=defaultdict(lambda:[0,0,0])
    for r in rows:
        k=(r.get('competence') or 'Sem competencia')[:7]
        months[k][0]+=1;months[k][1]+=r['amount_cents'];months[k][2]+=r['iss_cents']
    for k,(n,amount,iss) in sorted(months.items()):by_month.append([k,n,amount/100,iss/100])
    bio=BytesIO();wb.save(bio);return bio.getvalue()


def as_pdf(summary, rows)->bytes:
    buff=BytesIO()
    doc=SimpleDocTemplate(buff,pagesize=landscape(A3),leftMargin=23,rightMargin=23,topMargin=82,bottomMargin=33,
            title=_title(summary['kind']),author='Codisplan NFS-e')
    styles=getSampleStyleSheet()
    header=Paragraph(html.escape(_title(summary['kind'])),styles['Heading1'])
    info=Paragraph(html.escape(summary['company']['name']+' - '+summary['company']['tax_id']+' | '+summary['start']+' a '+summary['end']) + '<br/>Quantidade: '+str(summary['count'])+' | Servicos: R$ '+summary['totals']['amount_cents']+' | ISS: R$ '+summary['totals']['iss_cents'],styles['Normal'])
    cols=['customer_id','customer_name','number','issued_at','competence','service_code','amount_cents','net_cents','iss_cents','iss_retention_code','status']
    titles=['CPF/CNPJ','Tomador','NFS-e','Emissao','Competencia','Servico','Valor R$','Liquido R$','ISS R$','Retido','Situacao']
    widths=[98,232,88,87,88,80,90,90,89,65,78]
    # Resto da largura para tomador; tabela legivel em A3 horizontal.
    data=[[Paragraph(html.escape(t), styles['Normal']) for t in titles]]
    for r in rows:
        data.append([Paragraph(html.escape(_cell(r,c)),styles['Normal']) if c in ('customer_name',) else _cell(r,c) for c in cols])
    data.append(['TOTAL',str(len(rows)),'','','','',summary['totals']['amount_cents'],summary['totals']['net_cents'],summary['totals']['iss_cents'],'',''])
    table=LongTable(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E1E5EB')),
        ('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#EDEFF3')),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTNAME',(0,-1),(-1,-1),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),9.5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEBELOW',(0,0),(-1,0),0.6,colors.grey),
        ('LINEBELOW',(0,-1),(-1,-1),0.6,colors.grey),
        ('ROWBACKGROUNDS',(0,1),(-1,-2),[colors.white,colors.HexColor('#F7F8FA')]),
        ('ALIGN',(6,1),(8,-1),'RIGHT'),
    ]))
    def decorate(canvas,docobj):
        canvas.saveState()
        canvas.setFont('Helvetica-Bold',15)
        canvas.drawString(24,796,_title(summary['kind']))
        canvas.setFont('Helvetica',9)
        canvas.drawString(24,778,summary['company']['name']+' - '+summary['company']['tax_id']+' | '+summary['start']+' a '+summary['end'])
        canvas.drawString(24,764,'Quantidade: '+str(summary['count'])+' | Servicos: R$ '+summary['totals']['amount_cents']+' | ISS: R$ '+summary['totals']['iss_cents'])
        canvas.setStrokeColor(colors.HexColor('#d0d7e0'))
        canvas.line(24,749,1165,749)
        canvas.setFont('Helvetica',8)
        canvas.drawString(24,17,'Codisplan - Relatorio fiscal de conferencia | Fonte: XMLs sincronizados do ADN')
        canvas.drawRightString(1165,17,f'Pagina {docobj.page}')
        canvas.restoreState()
    doc.build([table],onFirstPage=decorate,onLaterPages=decorate)
    return buff.getvalue()
