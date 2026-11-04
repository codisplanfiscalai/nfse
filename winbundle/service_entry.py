"""Independent Windows Service process, no logged-in desktop session required."""
from __future__ import annotations
import os
from pathlib import Path
import sys
import threading
import win32event
import win32service
import win32serviceutil
import servicemanager
import uvicorn
from src.nfse.api import build_app


class NFSeWindowsService(win32serviceutil.ServiceFramework):
    _svc_name_='CodisplanNFSe'
    _svc_display_name_='Codisplan NFS-e - Servico Fiscal'
    _svc_description_='API ADN e portal administrativo Codisplan NFS-e em segundo plano.'
    def __init__(self,args):
        super().__init__(args)
        self.stop_event=win32event.CreateEvent(None,0,0,None)
        self.server=None
        self.thread=None
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.server:self.server.should_exit=True
        win32event.SetEvent(self.stop_event)
    def SvcDoRun(self):
        folder=Path(os.getenv('PROGRAMDATA',r'C:\ProgramData'))/'Codisplan'/'NFSe'
        cfg=folder/'desktop.json';port=8765
        if cfg.is_file():
            import json
            try:port=int(json.loads(cfg.read_text(encoding='utf-8')).get('port',8765))
            except (ValueError,OSError):pass
        os.environ['NFSE_DATA_DIR']=str(folder)
        app=build_app()
        self.server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,
                                                  access_log=False,log_level='warning',workers=1))
        self.server.run()


def main():
    if len(sys.argv)==1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(NFSeWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:win32serviceutil.HandleCommandLine(NFSeWindowsService)

if __name__=='__main__':main()
