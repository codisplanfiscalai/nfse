"""Isolated visual QA. Mocks transport only; backend API has independent tests."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORTAL=ROOT/'src/nfse/portal'

def check(screenshots:Path):
    screenshots.mkdir(parents=True,exist_ok=True)
    html='<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><div id="app"></div></body></html>'
    mock=r'''window.fetch=async (path,opts)=>{
       const s=String(path); let data=[];
       if(s.includes('/status'))data={product:'Codisplan NFS-e',configured:true,version:'0.3.0-dev.1.1'};
       else if(s.includes('/auth/me'))data={user:{id:1,name:'Operador Fiscal',email:'contato@example.test',role:'admin'},csrf:'qa-csrf',permissions:['dashboard','companies','certificates','sync','documents','reports','users','settings','audit']};
       else if(s.includes('/dashboard'))data={companies:3,invoices:1324,events:18,sync_runs:35,latest:[{id:2,company:'Empresa Exemplo',started_at:'2026-11-04T12:00:00Z',fetched:15,inserted:12,status:'CONCLUIDA'}]};
       else if(s.endsWith('/companies'))data=[{id:1,name:'Empresa Exemplo Ltda',identifier:'11222333000181',active:true}];
       else if(s.endsWith('/certificates'))data=[{id:1,label:'Certificado Empresarial',identity:'EMPRESA EXEMPLO',expires_at:'2027-06-01T12:00:00Z'}];
       else if(s.endsWith('/sync'))data=[{id:12,started_at:'2026-11-04T12:00:00Z',fetched:22,inserted:21,status:'CONCLUIDA',diagnostic:''}];
       else if(s.includes('/reports/'))data={count:1,totals:{service_cents:120000,iss_withheld_cents:2500},by_status:{ATIVA:1,CANCELADA:0,SUBSTITUIDA:0},rows:[{invoice_number:'124',issued_on:'2026-11-04',competence_on:'2026-11-01',recipient_name:'Cliente Exemplo',service_cents:120000,iss_withheld_cents:2500,status:'ATIVA'}],warning:'Relatório de demonstração.'};
       else if(s.includes('/documents?'))data=[];
       else if(s.endsWith('/settings'))data={adn_url:'https://api.nfse.gov.br/'};
       else if(s.endsWith('/users'))data=[{id:1,name:'Operador Fiscal',email:'contato@example.test',role:'admin'}];
       return new Response(JSON.stringify({data}),{status:200,headers:{'Content-Type':'application/json'}});
     };'''
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium') or None,args=['--no-sandbox'])
        errors=[]
        for label,width,height in [('desktop',1440,900),('mobile',390,844)]:
            page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
            page.on('pageerror',lambda e: errors.append(str(e)))
            page.set_content(html)
            page.add_style_tag(content=(PORTAL/'app.css').read_text(encoding='utf-8'))
            page.evaluate(mock)
            for file in ('vue.js','render.js','app.js'):
                page.add_script_tag(content=(PORTAL/file).read_text(encoding='utf-8'))
            page.get_by_text('Sincronizações recentes').wait_for(timeout=10000)
            # about:blank test page cannot resolve absolute /static assets.
            # Inject the real release icon so screenshot QA includes new branding.
            import base64
            img='data:image/png;base64,'+base64.b64encode((PORTAL/'app.png').read_bytes()).decode('ascii')
            page.locator('img.brand-icon').evaluate('(node,src)=>node.src=src',img)
            page.screenshot(path=str(screenshots/(label+'-dashboard.png')),full_page=True)
            if label=='mobile':page.get_by_role('button',name='Abrir menu').click()
            page.get_by_role('button',name='Relatórios fiscais').click()
            page.get_by_role('heading',name='Relatórios fiscais').first.wait_for(timeout=10000)
            page.screenshot(path=str(screenshots/(label+'-reports.png')),full_page=True)
            if not page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'):
                raise AssertionError('Horizontal overflow on '+label)
            page.close()
        browser.close()
        assert not errors,errors
    print('PASS: desktop 1440 and mobile 390 dashboard/reports; no JS errors or horizontal overflow.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--screenshots',type=Path,default=Path('artifacts/portal-screenshots'))
    args=parser.parse_args();check(args.screenshots)
