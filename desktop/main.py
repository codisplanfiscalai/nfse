"""Janela nativa Windows com system tray, webview Vue e controle grafico do servico.

Este executavel contem varios modos INTERNOS para o SCM/compilacao.
O usuario nao precisa abrir Prompt, PowerShell ou executar comandos.
"""
from __future__ import annotations
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def bundled(relative):
    return Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1])) / relative


def ping():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8765/api/health',timeout=.4) as r:
            return r.status==200
    except Exception:return False


def elevated(action):
    import ctypes
    action_map={'install':'--install-service','start':'--start-service','stop':'--stop-service',
       'restart':'--restart-service','uninstall':'--uninstall-service'}
    code=ctypes.windll.shell32.ShellExecuteW(None,'runas',sys.executable,action_map[action],None,0)
    if code<=32:raise OSError('Permissao administrativa nao concedida')


def desktop_app():
    from PySide6.QtCore import Qt,QTimer,QUrl
    from PySide6.QtGui import QAction,QIcon
    from PySide6.QtWidgets import QApplication,QMainWindow,QSystemTrayIcon,QMenu,QToolBar,QLabel,QMessageBox
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        QWebEngineView=None
    app=QApplication(sys.argv)
    app.setApplicationName('Codisplan NFS-e')
    app.setQuitOnLastWindowClosed(False)
    icon=QIcon(str(bundled('assets/app.ico')))
    app.setWindowIcon(icon)
    # Inicializacao automatica da GUI de bandeja na sessao do usuario.
    # Nao afeta o servico, que possui inicializacao automatica independente.
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
           r'Software\Microsoft\Windows\CurrentVersion\Run',0,winreg.KEY_SET_VALUE) as registry:
            winreg.SetValueEx(registry,'CodisplanNFSe',0,winreg.REG_SZ,'"'+sys.executable+'"')
    except OSError:
        pass
    local_process=[None]

    def ensure_backend():
        if ping():return
        if local_process[0] is None or local_process[0].poll() is not None:
            flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
            local_process[0]=subprocess.Popen([sys.executable,'--local-server'],creationflags=flags,
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    ensure_backend()

    class Main(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('Codisplan NFS-e | Painel Administrativo')
            self.resize(1320,830)
            self.setMinimumSize(900,580)
            toolbar=QToolBar('Serviço Windows',self)
            toolbar.setMovable(False)
            self.addToolBar(toolbar)
            toolbar.addWidget(QLabel('  SERVIÇO WINDOWS   '))
            for label,action in [('Instalar','install'),('Iniciar','start'),('Parar','stop'),('Reiniciar','restart'),('Desinstalar','uninstall')]:
                item=QAction(label,self)
                item.triggered.connect(lambda checked=False,a=action:self.manage(a))
                toolbar.addAction(item)
            self.statusBar().showMessage('Verificando o servidor de integração...')
            self._was_online=False
            if QWebEngineView:
                self.web=QWebEngineView(self)
                self.setCentralWidget(self.web)
                self.web.load(QUrl('http://127.0.0.1:8765/'))
            else:
                from PySide6.QtWidgets import QPushButton,QWidget,QVBoxLayout
                root=QWidget(self);layout=QVBoxLayout(root)
                layout.addWidget(QLabel('Instale o componente QtWebEngine para visualizar o painel embutido.'))
                open_button=QPushButton('Abrir painel no navegador');open_button.clicked.connect(self.open_browser)
                layout.addWidget(open_button);self.setCentralWidget(root)
            self.timer=QTimer(self)
            self.timer.timeout.connect(self.heartbeat)
            self.timer.start(3500)
            self.heartbeat()

        def open_browser(self):
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl('http://127.0.0.1:8765/'))

        def manage(self,action):
            if action=='install' and local_process[0] and local_process[0].poll() is None:
                local_process[0].terminate()
                try:local_process[0].wait(timeout=4)
                except subprocess.TimeoutExpired:local_process[0].kill()
            try:
                elevated(action)
                QMessageBox.information(self,'Serviço Windows',
                    f'Ação "{action}" solicitada ao Windows. A atualização do status é automática.')
            except Exception as exc:QMessageBox.warning(self,'Serviço Windows',str(exc))
            QTimer.singleShot(4000,self.heartbeat)

        def heartbeat(self):
            online=ping()
            self.statusBar().showMessage('Integração ativa em 127.0.0.1:8765' if online else 'Serviço indisponível - use Iniciar ou Instalar')
            tray.setToolTip('Codisplan NFS-e - '+('ativo' if online else 'inativo'))
            if online and not self._was_online and QWebEngineView:
                self.web.reload()
            self._was_online=online

        def closeEvent(self,event):
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.hide();event.ignore()
                if not self._shown:
                    tray.showMessage('Codisplan NFS-e','Aplicativo continua em segundo plano.',QSystemTrayIcon.Information,3000)
                    self._shown=True
            else:event.accept()
        _shown=False

    tray=QSystemTrayIcon(icon,app)
    main=Main()
    menu=QMenu()
    show=menu.addAction('Abrir painel administrativo')
    show.triggered.connect(lambda: (main.showNormal(),main.activateWindow()))
    menu.addSeparator()
    start=menu.addAction('Iniciar serviço Windows')
    start.triggered.connect(lambda:main.manage('start'))
    restart=menu.addAction('Reiniciar serviço')
    restart.triggered.connect(lambda:main.manage('restart'))
    menu.addSeparator()
    exit_app=menu.addAction('Sair da interface')
    def finish():
        if local_process[0] and local_process[0].poll() is None:
            local_process[0].terminate()
        tray.hide();app.quit()
    exit_app.triggered.connect(finish)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: main.showNormal() if reason==QSystemTrayIcon.DoubleClick else None)
    tray.show()
    main.show()
    sys.exit(app.exec())


def main():
    args=sys.argv[1:]
    if args==['--self-test']:
        # Verificacao interna usada pelo runner Windows; nao e interface de operacao.
        from nfse_core.api import app
        from PySide6.QtGui import QIcon
        from PySide6.QtWebEngineWidgets import QWebEngineView
        assert app.title == 'Codisplan NFS-e API'
        assert bundled('assets/app.ico').is_file()
        assert bundled('frontend/index.html').is_file()
        assert bundled('frontend/logo-mark.png').is_file()
        print('Codisplan NFS-e: validacao do executavel concluida')
        return 0
    if args and args[0]=='--service':
        from desktop.service import start_service_dispatcher
        return start_service_dispatcher()
    if args and args[0]=='--local-server':
        from run_server import serve
        return serve()
    for action in ('install','start','stop','restart','uninstall'):
        if args==['--'+action+'-service']:
            from desktop.service import control
            try:control(action)
            except Exception as e:
                import ctypes
                ctypes.windll.user32.MessageBoxW(None,str(e),'Codisplan NFS-e - Serviço',0x10)
                return 1
            return 0
    return desktop_app()

if __name__=='__main__':main()
