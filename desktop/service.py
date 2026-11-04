"""Servico Windows real, separado do aplicativo tray (Session 0 nao possui UI)."""
from __future__ import annotations
import sys
from pathlib import Path

import win32event
import win32service
import win32serviceutil
import servicemanager
import uvicorn

from nfse_core.api import app
from nfse_core.settings import HOST,PORT

SERVICE_NAME='CodisplanNFSe'
DISPLAY_NAME='Codisplan NFS-e - Servico de Integracao'


class NfseWindowsService(win32serviceutil.ServiceFramework):
    _svc_name_=SERVICE_NAME
    _svc_display_name_=DISPLAY_NAME
    _svc_description_='Distribuicao ADN e relatorios de notas fiscais de servicos.'

    def __init__(self,args):
        super().__init__(args)
        self.stop_event=win32event.CreateEvent(None,0,0,None)
        self.server=None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.server:self.server.should_exit=True
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg('Codisplan NFS-e - servico iniciado')
        config=uvicorn.Config(app,host=HOST,port=PORT,log_level='warning',access_log=False)
        self.server=uvicorn.Server(config)
        try:self.server.run()
        finally:servicemanager.LogInfoMsg('Codisplan NFS-e - servico finalizado')


def start_service_dispatcher():
    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(NfseWindowsService)
    servicemanager.StartServiceCtrlDispatcher()


def install():
    # Instalacao por processo elevado iniciado pelo botao na GUI, sem terminal.
    from nfse_core.settings import ROOT
    import subprocess
    ROOT.mkdir(parents=True,exist_ok=True)
    subprocess.run(['icacls',str(ROOT),'/inheritance:r','/grant:r','*S-1-5-18:(OI)(CI)F','*S-1-5-32-544:(OI)(CI)F'],
                   check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    win32serviceutil.InstallService(
        'desktop.service.NfseWindowsService',SERVICE_NAME,DISPLAY_NAME,
        startType=win32service.SERVICE_AUTO_START,
        exeName=sys.executable,exeArgs='--service',
        description=NfseWindowsService._svc_description_)
    win32serviceutil.StartService(SERVICE_NAME)


def control(action):
    if action=='install':return install()
    if action=='start':return win32serviceutil.StartService(SERVICE_NAME)
    if action=='stop':return win32serviceutil.StopService(SERVICE_NAME)
    if action=='restart':return win32serviceutil.RestartService(SERVICE_NAME)
    if action=='uninstall':
        try:win32serviceutil.StopService(SERVICE_NAME)
        except Exception:pass
        return win32serviceutil.RemoveService(SERVICE_NAME)
    raise ValueError('Comando de servico invalido')
