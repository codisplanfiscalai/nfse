"""Entrypoint interno do binario/servico. Nao e interface de operacao do usuario."""
from nfse_core.settings import HOST,PORT
from nfse_core.api import app
import uvicorn


def serve():
    uvicorn.run(app,host=HOST,port=PORT,log_level='warning',access_log=False)

if __name__=='__main__':serve()
