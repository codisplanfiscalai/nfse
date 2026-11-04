"""Main server for Windows GUI, Windows Service or Docker."""
from __future__ import annotations
import os
import uvicorn
from .api import build_app


def serve(host='127.0.0.1', port=8765):
    uvicorn.run(build_app(),host=host,port=int(port),log_level='warning',access_log=False)

if __name__=='__main__':
    serve(os.getenv('NFSE_HOST','127.0.0.1'),int(os.getenv('NFSE_PORT','8765')))
