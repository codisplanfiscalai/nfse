"""Codisplan NFS-e graphical launcher: the API belongs to this tray process."""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import webbrowser

from .local_runtime import LocalPortalRuntime
from .windows_tray import Tray
from src.nfse.api import build_app
from src.nfse.settings import bundled, data_directory

PRODUCT = 'Codisplan NFS-e'
BG = '#F4F6FF'
SIDE = '#191C49'
PANEL = '#FFFFFF'
INK = '#24254B'
MUTED = '#626985'
ACCENT = '#5A51DF'
MINT = '#35DAC6'


def exe_dir() -> Path:
    return Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]


def desktop_config_file() -> Path:
    return data_directory() / 'desktop.json'


def read_config() -> dict:
    try:
        data = json.loads(desktop_config_file().read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def icon_file() -> Path:
    icon = bundled('assets/app.ico')
    if not icon.exists():
        icon = exe_dir() / 'assets' / 'app.ico'
    return icon


def probe(port: int) -> bool:
    """The button opens the browser only after our own uvicorn reports started."""
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/health/ready', timeout=0.45) as response:
            return response.status == 200
    except (OSError, ValueError):
        return False


def single_instance():
    """A second double-click must not create a second tray/server instance."""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel.CreateMutexW(None, False, 'Local\\CodisplanNFSe-Desktop-v2')
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    return handle, ctypes.get_last_error() == 183


def main() -> None:
    if sys.platform != 'win32':
        raise RuntimeError('O aplicativo gráfico é destinado ao Windows.')
    mutex, already_running = single_instance()
    if already_running:
        messagebox.showinfo(PRODUCT, 'O NFS-e já está aberto na área de notificação do Windows. Abra-o pelo ícone próximo ao relógio.')
        return

    settings = read_config()
    port_value = settings.get('port', 8765)
    try:
        initial_port = int(port_value)
        if not 1024 <= initial_port <= 65535:
            raise ValueError()
    except (TypeError, ValueError):
        initial_port = 8765
    os.environ['NFSE_DATA_DIR'] = str(data_directory())
    runtime = LocalPortalRuntime(build_app)

    root = tk.Tk()
    root.title(PRODUCT + ' | Administração')
    root.geometry('1060x700')
    root.minsize(800, 560)
    root.configure(bg=BG)
    ico = icon_file()
    if ico.exists():
        root.iconbitmap(str(ico))
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TFrame', background=BG)
    style.configure('TLabel', background=BG, foreground=INK, font=('Segoe UI', 10))
    style.configure('TButton', background=PANEL, foreground=INK, font=('Segoe UI', 10), padding=(15, 11))
    style.map('TButton', background=[('active', '#E8E9FF')])
    style.configure('TNotebook', background=BG, borderwidth=0)
    style.configure('TNotebook.Tab', font=('Segoe UI', 10), padding=(17, 11))
    style.map('TNotebook.Tab', background=[('selected', '#E7E5FF')], foreground=[('selected', '#342D9B')])
    style.configure('Primary.TButton', background=ACCENT, foreground='#FFFFFF', font=('Segoe UI', 10, 'bold'), padding=(17, 12))
    style.map('Primary.TButton', background=[('active', '#4137B8')], foreground=[('active', '#FFFFFF')])

    sidebar = tk.Frame(root, bg=SIDE, width=245)
    sidebar.pack(side='left', fill='y')
    sidebar.pack_propagate(False)
    brand = bundled('assets/app.png')
    if brand.exists():
        from PIL import Image, ImageTk
        photo = ImageTk.PhotoImage(Image.open(brand).convert('RGBA').resize((69, 69)))
        brand_image = tk.Label(sidebar, image=photo, bg=SIDE)
        brand_image.image = photo
        brand_image.pack(anchor='w', padx=25, pady=(28, 7))
    tk.Label(sidebar, text='NFS-e', font=('Segoe UI', 27, 'bold'), bg=SIDE, fg='white').pack(anchor='w', padx=25)
    tk.Label(sidebar, text='CODISPLAN  /  GESTÃO FISCAL', font=('Segoe UI', 9, 'bold'), bg=SIDE, fg='#A8B2F6').pack(anchor='w', padx=25, pady=(0, 38))
    for item in ('AMBIENTE LOCAL', 'Painel administrativo', 'Certificados digitais', 'Distribuição ADN', 'Relatórios fiscais'):
        tk.Label(sidebar, text=item, font=('Segoe UI', 10), bg=SIDE,
                 fg=MINT if item == 'AMBIENTE LOCAL' else '#E5E7FF', anchor='w').pack(anchor='w', padx=25, pady=7)
    tk.Label(sidebar, text='Sem instalação de serviço.\nPermanece ativo na bandeja\naté você escolher Sair.',
             font=('Segoe UI', 9), bg=SIDE, fg='#B9C2F1', justify='left').pack(side='bottom', anchor='w', padx=25, pady=30)

    body = ttk.Frame(root, padding=29)
    body.pack(fill='both', expand=True)
    tk.Label(body, text='Central de administração', font=('Segoe UI', 22, 'bold'),
             bg=BG, fg=INK).pack(anchor='w')
    state = tk.StringVar(value='Iniciando portal local...')
    tk.Label(body, textvariable=state, font=('Segoe UI', 10), bg=BG,
             fg=MUTED).pack(anchor='w', pady=(8, 22))
    tabs = ttk.Notebook(body)
    tabs.pack(fill='both', expand=True)
    main_page = ttk.Frame(tabs, padding=26)
    settings_page = ttk.Frame(tabs, padding=26)
    history_page = ttk.Frame(tabs, padding=26)
    tabs.add(main_page, text='Serviços e conexões')
    tabs.add(settings_page, text='Configuração local')
    tabs.add(history_page, text='Informações')
    text = tk.Label(main_page, text='Servidor do NFS-e executado pelo aplicativo, sem exigir administrador ou instalação.',
                    bg=BG, fg=INK, font=('Segoe UI', 11), justify='left', wraplength=595)
    text.pack(anchor='w', pady=(0, 17))
    status = tk.StringVar(value='Preparando ambiente...')
    tk.Label(main_page, textvariable=status, bg=BG, fg=MUTED, font=('Segoe UI', 10),
             justify='left', wraplength=590).pack(anchor='w', pady=(0, 23))
    port = tk.IntVar(value=initial_port)
    ttk.Label(settings_page, text='Porta do portal local (somente 127.0.0.1)').pack(anchor='w')
    ttk.Entry(settings_page, textvariable=port, width=12).pack(anchor='w', pady=(10, 17))
    ttk.Label(settings_page, text='O portal inicia automaticamente quando você abre o NFS-e.\nNão é instalado um serviço do Windows.').pack(anchor='w')
    ttk.Label(history_page, text='Codisplan NFS-e  ·  Edição para Windows', font=('Segoe UI', 15, 'bold')).pack(anchor='w')
    ttk.Label(history_page, text='Portal Vue 3 · FastAPI local · autenticação ADN com certificado A1').pack(anchor='w', pady=12)
    ttk.Label(history_page, text='Os dados fiscais são armazenados localmente no perfil do usuário.').pack(anchor='w', pady=12)
    footer = tk.Frame(body, bg=BG)
    footer.pack(fill='x', pady=(19, 0))
    tray = None
    exiting = False
    notified = False
    prev_state = None

    def update_status():
        nonlocal prev_state, notified
        if exiting:
            return
        if runtime.active:
            active = 'active'
            state.set(f'Portal ativo · http://127.0.0.1:{runtime.port}')
            status.set('Servidor local em execução, disponível no navegador e na área de notificação.')
            if not notified and tray and tray.available:
                tray.notify('Portal NFS-e ativo. Abra pelo menu do ícone na bandeja.')
                notified = True
        elif runtime.running:
            active = 'starting'
            state.set('Iniciando ambiente local...')
            status.set('Preparando acesso e verificando a porta HTTP.')
        elif runtime.error:
            active = 'error'
            state.set('Não foi possível iniciar o portal')
            status.set(runtime.error)
        else:
            active = 'stopped'
            state.set('Portal interrompido')
            status.set('Clique em Iniciar para reativar sem instalar nenhum serviço.')
        prev_state = active
        root.after(600, update_status)

    def start_server():
        try:
            runtime.start(port.get())
            update_status_immediate()
        except Exception as exc:
            runtime.error = str(exc)
            if not os.environ.get('NFSE_SMOKE_STATUS_FILE'):
                messagebox.showerror(PRODUCT, str(exc), parent=root)

    def update_status_immediate():
        if runtime.active:
            state.set(f'Portal ativo · http://127.0.0.1:{runtime.port}')

    def stop_server():
        try:
            runtime.stop()
            status.set('Servidor local interrompido.')
        except Exception as exc:
            messagebox.showerror(PRODUCT, str(exc), parent=root)

    def restart_server():
        try:
            runtime.restart(int(port.get()))
            status.set('Reiniciando o portal...')
        except Exception as exc:
            messagebox.showerror(PRODUCT, str(exc), parent=root)

    def open_panel():
        try:
            if not runtime.running:
                runtime.start(port.get())
            if runtime.active and probe(runtime.port):
                webbrowser.open(f'http://127.0.0.1:{runtime.port}/')
            else:
                pending_open(0)
        except Exception as exc:
            messagebox.showerror(PRODUCT, str(exc), parent=root)

    def pending_open(attempt):
        if exiting:
            return
        if runtime.active and probe(runtime.port):
            webbrowser.open(f'http://127.0.0.1:{runtime.port}/')
        elif attempt >= 24 or (not runtime.running and runtime.error):
            messagebox.showerror(PRODUCT, runtime.error or 'O portal não respondeu. Confira a porta na configuração.', parent=root)
        else:
            root.after(250, lambda: pending_open(attempt + 1))

    actions = ttk.Frame(main_page)
    actions.pack(anchor='w', pady=(6, 16))
    for label, callback in (('Iniciar', start_server), ('Interromper', stop_server), ('Reiniciar', restart_server), ('Abrir portal', open_panel)):
        ttk.Button(actions, text=label, command=callback,
                   style='Primary.TButton' if label == 'Abrir portal' else 'TButton').pack(side='left', padx=(0, 8))
    ttk.Button(footer, text='Abrir portal no navegador', style='Primary.TButton', command=open_panel).pack(side='left')

    def save_settings():
        try:
            new_port = int(port.get())
            if not 1024 <= new_port <= 65535:
                raise ValueError('Informe uma porta entre 1024 e 65535.')
            f = desktop_config_file()
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps({'port': new_port}, indent=2), encoding='utf-8')
            runtime.restart(new_port)
            messagebox.showinfo(PRODUCT, 'Porta salva e portal reiniciado.', parent=root)
        except Exception as exc:
            messagebox.showerror(PRODUCT, str(exc), parent=root)

    ttk.Button(settings_page, text='Salvar e aplicar', command=save_settings).pack(anchor='w', pady=(22, 0))

    def show():
        root.deiconify()
        root.lift()
        root.focus_force()

    def hide():
        if tray and tray.available:
            root.withdraw()
        else:
            root.iconify()

    def quit_all():
        nonlocal exiting
        exiting = True
        if tray:
            tray.close()
        runtime.stop()
        root.destroy()

    callbacks = {
        1: ('Abrir administração', show),
        2: ('Abrir portal NFS-e', open_panel),
        3: ('Iniciar portal', start_server),
        4: ('Interromper portal', stop_server),
        5: ('Reiniciar portal', restart_server),
        6: ('Sair do NFS-e', quit_all),
    }
    try:
        tray = Tray(root, ico, callbacks, 'CodisplanNFSe')
    except Exception as exc:
        status.set(f'Área de notificação indisponível: {exc}')
        tray = None
    root.protocol('WM_DELETE_WINDOW', hide)
    root.bind('<Escape>', lambda _: hide())
    root.after(100, start_server)
    root.after(300, update_status)

    # Native smoke test also verifies actual local HTTP startup, not just a Tk window.
    smoke_file = os.environ.get('NFSE_SMOKE_STATUS_FILE')
    if smoke_file:
        def smoke(attempt=0):
            if not runtime.active and runtime.running and attempt < 32:
                root.after(250, lambda: smoke(attempt + 1))
                return
            check = ctypes.windll.kernel32.GetConsoleWindow()
            result = {
                'tk_window': bool(root.winfo_exists()),
                'tray_window': bool(tray and tray.window),
                'tray_available': bool(tray and tray.available),
                'console_window': bool(check),
                'http_ready': bool(runtime.active and probe(runtime.port)),
                'no_windows_service': True,
            }
            Path(smoke_file).write_text(json.dumps(result), encoding='utf-8')
            quit_all()
        root.after(500, smoke)
    root.mainloop()
    # Hold the kernel mutex until the GUI exits, including tray-only operation.
    ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(mutex))


if __name__ == '__main__':
    main()
