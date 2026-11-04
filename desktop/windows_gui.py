"""Windows GUI administration; user never needs command line."""
from __future__ import annotations
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import ttk,messagebox
import webbrowser
from .windows_tray import Tray
from src.nfse.settings import bundled

PRODUCT='Codisplan NFS-e'
SERVICE='CodisplanNFSe'


def exe_dir():
    return Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]


def install_service():
    service_bin=exe_dir()/'CodisplanNFSeServico.exe'
    if not service_bin.is_file():
        raise FileNotFoundError('Executável do serviço ausente. Reinstale o pacote Windows completo.')
    # Native Windows UAC prompt; no terminal opens for end users.
    params='install --startup auto'
    result=ctypes.windll.shell32.ShellExecuteW(None,'runas',str(service_bin),params,str(exe_dir()),0)
    if result<=32:raise OSError('Instalação não autorizada ou indisponível.')


def service_command(command):
    if command not in ('start','stop','query'):raise ValueError('Comando de serviço inválido.')
    result=subprocess.run(['sc.exe',command,SERVICE],capture_output=True,text=True,
                          encoding='utf-8',errors='replace',timeout=15,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    return result.returncode,result.stdout+'\n'+result.stderr


def main():
    if sys.platform!='win32':raise RuntimeError('O painel nativo só é executado no Windows.')
    root=tk.Tk();root.title(PRODUCT+' | Administração');root.geometry('1050x690');root.minsize(790,540)
    root.configure(bg='#f5f7f8')
    ico=bundled('assets/app.ico')
    if not ico.exists():ico=exe_dir()/'assets'/'app.ico'
    if ico.exists():root.iconbitmap(str(ico))
    style=ttk.Style(root);style.theme_use('clam');style.configure('TFrame',background='#f5f7f8')
    style.configure('TLabel',background='#f5f7f8',foreground='#244d58',font=('Segoe UI',10))
    style.configure('TButton',font=('Segoe UI',10),padding=(15,10))
    style.configure('TNotebook.Tab',font=('Segoe UI',10),padding=(15,10))
    side=tk.Frame(root,bg='#064d5d',width=240);side.pack(side='left',fill='y');side.pack_propagate(False)
    tk.Label(side,text='Codisplan',font=('Segoe UI',23,'bold'),bg='#064d5d',fg='white').pack(anchor='w',padx=24,pady=(34,3))
    tk.Label(side,text='NFS-e | ADMINISTRAÇÃO',font=('Segoe UI',9,'bold'),bg='#064d5d',fg='#99cbd5').pack(anchor='w',padx=24)
    tk.Label(side,text='Portal responsivo\nCertificados digitais\nDistribuição ADN\nRelatórios fiscais\nServiço em segundo plano',bg='#064d5d',fg='#f1f8f9',font=('Segoe UI',11),justify='left').pack(anchor='w',padx=24,pady=(65,0))
    tk.Label(side,text='O fechamento da janela\nnão encerra o serviço.',bg='#064d5d',fg='#acd1d8',font=('Segoe UI',9),justify='left').pack(side='bottom',anchor='w',padx=24,pady=30)
    body=ttk.Frame(root,padding=27);body.pack(fill='both',expand=True)
    tk.Label(body,text='Controle do ambiente',bg='#f5f7f8',fg='#064d5d',font=('Segoe UI',20,'bold')).pack(anchor='w')
    state=tk.StringVar(value='Consultando serviço...')
    tk.Label(body,textvariable=state,bg='#f5f7f8',fg='#456e77',font=('Segoe UI',10)).pack(anchor='w',pady=(9,18))
    tabs=ttk.Notebook(body);tabs.pack(fill='both',expand=True)
    service_page=ttk.Frame(tabs,padding=24);settings_page=ttk.Frame(tabs,padding=24);about_page=ttk.Frame(tabs,padding=24)
    tabs.add(service_page,text='Serviço Windows');tabs.add(settings_page,text='Conexão local');tabs.add(about_page,text='Sobre')
    status=tk.StringVar(value='')
    label=ttk.Label(service_page,text='O serviço funciona independentemente da janela, com inicialização automática pelo Windows.')
    label.pack(anchor='w',pady=(0,20))
    tk.Label(service_page,textvariable=status,bg='#f5f7f8',fg='#326373',font=('Consolas',10),justify='left',wraplength=600).pack(fill='x',anchor='w',pady=(12,19))
    port_file=Path(os.getenv('PROGRAMDATA',str(Path.home())))/'Codisplan'/'NFSe'/'desktop.json'
    config={}
    if port_file.exists():
        try:config=json.loads(port_file.read_text(encoding='utf-8'))
        except (OSError,ValueError):pass
    port=tk.IntVar(value=int(config.get('port',8765)))
    ttk.Label(settings_page,text='Porta local do painel web').pack(anchor='w')
    entry=ttk.Entry(settings_page,textvariable=port,width=12);entry.pack(anchor='w',pady=(7,15))
    ttk.Label(settings_page,text='Servidor limitado ao endereço 127.0.0.1. Para acesso de rede, use uma instalação segura com proxy HTTPS.').pack(anchor='w')
    ttk.Label(about_page,text='Codisplan NFS-e | Gestão Fiscal',font=('Segoe UI',16,'bold')).pack(anchor='w')
    ttk.Label(about_page,text='API ADN · mTLS ICP-Brasil A1 · XML/GZip · Serviços prestados, ISS retido e eventos').pack(anchor='w',pady=15)
    ttk.Label(about_page,text='Produto em desenvolvimento. Consulte os XMLs e valide a cobertura dos NSUs antes do fechamento fiscal.').pack(anchor='w')
    def refresh():
        code,output=service_command('query')
        if code:state.set('Serviço não instalado');status.set('Instale o serviço Windows para iniciar o portal.');return
        if 'RUNNING' in output:state.set('Serviço em execução');status.set('● Executando em segundo plano')
        elif 'STOPPED' in output:state.set('Serviço parado');status.set('● Instalado, aguardando início')
        else:state.set('Serviço em transição');status.set(output[-1200:])
    def action(operation):
        try:
            if operation=='install':install_service();messagebox.showinfo(PRODUCT,'Autorize a instalação e depois clique em Atualizar.',parent=root)
            else:
                code,out=service_command(operation)
                if code:raise RuntimeError(out[-700:])
            root.after(1200,refresh)
        except Exception as ex:messagebox.showerror(PRODUCT,str(ex),parent=root)
    buttons=ttk.Frame(service_page);buttons.pack(anchor='w',pady=(0,15))
    for text,fn in [('Instalar serviço','install'),('Iniciar','start'),('Parar','stop')]:
        ttk.Button(buttons,text=text,command=lambda x=fn:action(x)).pack(side='left',padx=(0,7))
    ttk.Button(service_page,text='Atualizar situação',command=refresh).pack(anchor='w')
    def open_panel():
        try:p=int(port.get())
        except Exception:p=8765
        webbrowser.open(f'http://127.0.0.1:{p}/')
    ttk.Button(body,text='Abrir painel administrativo Vue.js',command=open_panel).pack(anchor='w',pady=(16,0))
    def save_settings():
        try:
            value=int(port.get())
            if not 1024<=value<=65535:raise ValueError('Informe uma porta entre 1024 e 65535.')
            port_file.parent.mkdir(parents=True,exist_ok=True)
            port_file.write_text(json.dumps({'port':value},indent=2),encoding='utf-8')
            messagebox.showinfo(PRODUCT,'Configuração gravada. Reinicie o serviço para aplicar.',parent=root)
        except Exception as e:messagebox.showerror(PRODUCT,str(e),parent=root)
    ttk.Button(settings_page,text='Salvar configuração',command=save_settings).pack(anchor='w',pady=(20,0))
    tray=None
    def show():root.deiconify();root.lift();root.focus_force()
    def hide():root.withdraw() if tray and tray.available else root.iconify()
    def quit_gui():
        if tray:tray.close()
        root.destroy()
    callbacks={1:('Abrir administração',show),2:('Abrir painel Vue',open_panel),3:('Iniciar serviço',lambda:action('start')),
               4:('Parar serviço',lambda:action('stop')),5:('Atualizar',refresh),6:('Sair da interface',quit_gui)}
    try:tray=Tray(root,ico,callbacks,'NFSe')
    except Exception:tray=None
    root.protocol('WM_DELETE_WINDOW',hide)
    root.bind('<Escape>',lambda e:hide())
    root.after(200,refresh)
    status_file=os.environ.get('NFSE_SMOKE_STATUS_FILE')
    if status_file:
        def smoke_status():
            check=ctypes.windll.kernel32.GetConsoleWindow()
            Path(status_file).write_text(json.dumps({'tk_window':bool(root.winfo_exists()),'tray_window':bool(tray and tray.window),
                'tray_available':bool(tray and tray.available),'console_window':bool(check)}),encoding='utf-8')
            quit_gui()
        root.after(1600,smoke_status)
    root.mainloop()

if __name__=='__main__':main()
