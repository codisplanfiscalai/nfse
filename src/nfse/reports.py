"""Period reports, PDF/Excel/CSV with fiscal totals without float arithmetic."""
from __future__ import annotations
from collections import defaultdict
from datetime import date,datetime
from io import BytesIO,StringIO
import csv
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer,PageBreak
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.utils import get_column_letter
from .store import Store

REPORTS={'mensal':'Relatório de serviços prestados (emissão)',
         'competencia':'Relatório de serviços prestados (competência)',
         'iss-retido':'Relatório de ISS retido','canceladas':'Relatório de notas canceladas e substituídas'}
HEADERS=['Emissão','Competência','Nota','Tomador','CNPJ/CPF','Serviço','Valor serviços','Valor líquido','ISS','ISS retido','IRRF','INSS','PCC','Situação','Chave']
COLS=['issued_on','competence_on','invoice_number','recipient_name','recipient_identifier','service_description',
      'service_cents','net_cents','iss_cents','iss_withheld_cents','irrf_cents','inss_cents','pcc_cents','status','access_key']


def query_report(store:Store,company:int,kind:str,initial:str,final:str):
    if kind not in REPORTS:raise ValueError('Tipo de relatório inválido.')
    start,end=date.fromisoformat(initial),date.fromisoformat(final)
    if start>end or (end-start).days>366*5:raise ValueError('Período inválido ou maior que cinco anos.')
    c=store.row('SELECT * FROM companies WHERE id=?',(company,))
    if c is None:raise ValueError('Empresa não encontrada.')
    dim='issued_on' if kind in ('mensal','canceladas','iss-retido') else 'competence_on'
    sql=f"SELECT * FROM documents WHERE company_id=? AND document_type='NFSE' AND {dim} BETWEEN ? AND ? AND issuer_identifier=?"
    params=[company,initial,final,c['identifier']]
    if kind=='iss-retido':sql+=' AND iss_withheld_cents>0'
    if kind=='canceladas':sql+=" AND status IN ('CANCELADA','SUBSTITUIDA')"
    sql+=f' ORDER BY {dim},invoice_number,nsu'
    rows=store.rows(sql,params)
    sums={k:sum(int(row.get(k) or 0) for row in rows if row['status']=='ATIVA') for k in COLS if k.endswith('_cents')}
    totals_by_status={name:sum(1 for x in rows if x['status']==name) for name in ('ATIVA','CANCELADA','SUBSTITUIDA')}
    return {'company':{'name':c['name'],'identifier':c['identifier']},'kind':kind,'title':REPORTS[kind],
            'from':initial,'to':final,'count':len(rows),'totals':sums,'by_status':totals_by_status,'rows':rows,
            'dimension':dim,'warning':'Valores monetários dos documentos cancelados/substituídos não integram os totais vigentes.'}


def money(cents):return f'{int(cents)/100:,.2f}'.replace(',','|').replace('.',',').replace('|','.')


def excel(report):
    wb=Workbook();ws=wb.active;ws.title='Notas'
    ws.append([report['title']]);ws.append([report['company']['name']+' - '+report['company']['identifier']]);ws.append([report['from']+' a '+report['to']]);ws.append([]);ws.append(HEADERS)
    for d in report['rows']:
        ws.append([d.get(k) if not k.endswith('_cents') else int(d.get(k) or 0)/100 for k in COLS])
    ws.append([]);ws.append(['TOTAL VIGENTE','','','','','']+[report['totals'].get(k,0)/100 for k in ('service_cents','net_cents','iss_cents','iss_withheld_cents','irrf_cents','inss_cents','pcc_cents')])
    for cell in ws[5]:cell.fill=PatternFill('solid',fgColor='064D5D');cell.font=Font(bold=True,color='FFFFFF');cell.alignment=Alignment(wrap_text=True)
    for i in range(1,len(COLS)+1):ws.column_dimensions[get_column_letter(i)].width={4:27,6:32,15:44}.get(i,17)
    for row in ws.iter_rows(min_row=6,max_row=5+len(report['rows']),min_col=7,max_col=13):
        for cell in row:cell.number_format='#,##0.00'
    for name,value in [('Quantidade',report['count']),('Ativas',report['by_status']['ATIVA']),('Canceladas',report['by_status']['CANCELADA']),('Substituídas',report['by_status']['SUBSTITUIDA'])]:
        if 'Resumo' not in wb:wb.create_sheet('Resumo').append(['Indicador','Valor'])
        wb['Resumo'].append([name,value])
    for name,field in [('Por tomador','recipient_name'),('Por competência','competence_on'),('Por serviço','service_code')]:
        sheet=wb.create_sheet(name)
        sheet.append([name,'Quantidade','Serviços vigentes'])
        agg=defaultdict(lambda:[0,0])
        for row in report['rows']:
            key=row.get(field) or '(não informado)'
            agg[key][0]+=1
            if row['status']=='ATIVA':agg[key][1]+=int(row.get('service_cents') or 0)
        for key,(count,value) in sorted(agg.items()):sheet.append([key,count,value/100])
        sheet.column_dimensions['A'].width=38
        sheet.column_dimensions['C'].width=22
    buf=BytesIO();wb.save(buf);return buf.getvalue()


def csv_bytes(report):
    output=StringIO();writer=csv.writer(output,delimiter=';',lineterminator='\r\n')
    writer.writerow(HEADERS)
    for row in report['rows']:
        values=[money(row[k]) if k.endswith('_cents') else (row.get(k) or '') for k in COLS]
        # Neutralize formula injection while retaining identifiers as literal text.
        writer.writerow(["'"+x if isinstance(x,str) and x[:1] in ('=','+','-','@','\t','\r') else x for x in values])
    return ('\ufeff'+output.getvalue()).encode('utf-8')


def pdf(report):
    buf=BytesIO()
    document=SimpleDocTemplate(buf,pagesize=landscape(A4),rightMargin=30,leftMargin=30,topMargin=38,bottomMargin=36)
    style=ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=15,leading=19,textColor=colors.HexColor('#064D5D'))
    body=ParagraphStyle('body',fontName='Helvetica',fontSize=8,leading=11)
    elements=[Paragraph('CODISPLAN | NFS-e',style),Spacer(1,7),Paragraph(report['title'],style),
              Paragraph(f"{report['company']['name']} | {report['company']['identifier']} | {report['from']} a {report['to']}",body),Spacer(1,12)]
    headers=['Emissão','Competência','Nota','Tomador','CNPJ/CPF','Serviço','Serviços','Líquido','ISS retido','Situação']
    values=[headers]
    for d in report['rows']:
        def short(s,n):return (str(s or '')[:n]+'…') if len(str(s or ''))>n else str(s or '')
        values.append([d['issued_on'] or '',d['competence_on'] or '',short(d['invoice_number'],14),
                       short(d['recipient_name'],26),short(d['recipient_identifier'],18),short(d['service_description'],35),
                       money(d['service_cents']),money(d['net_cents']),money(d['iss_withheld_cents']),d['status']])
    if len(values)==1:values.append(['Nenhum documento no período.']+['']*9)
    widths=[58,59,37,123,83,140,64,63,62,72]
    table=Table(values,colWidths=widths,repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#064D5D')),
                               ('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                               ('FONTNAME',(0,1),(-1,-1),'Helvetica'),('FONTSIZE',(0,0),(-1,-1),7),
                               ('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),
                               ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#EDF3F3')]),
                               ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LINEBELOW',(0,0),(-1,0),0.7,colors.HexColor('#064D5D'))]))
    elements.append(table);elements.append(Spacer(1,12))
    elements.append(Paragraph('Total vigente de serviços: R$ '+money(report['totals']['service_cents'])+
                              '   |   ISS retido: R$ '+money(report['totals']['iss_withheld_cents'])+
                              '   |   Documentos: '+str(report['count']),body))
    elements.append(Paragraph(report['warning'],body))
    def footer(canv,doc):
        canv.setFont('Helvetica',8);canv.setFillColor(colors.HexColor('#47666E'))
        canv.drawString(30,23,'Relatório gerado a partir de XMLs armazenados. Verifique a cobertura da sincronização ADN.')
        canv.drawRightString(landscape(A4)[0]-30,23,f'Página {doc.page}')
    document.build(elements,onFirstPage=footer,onLaterPages=footer)
    return buf.getvalue()
