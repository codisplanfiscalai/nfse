from __future__ import annotations
import os
from pathlib import Path


def data_root() -> Path:
    defined = os.getenv('CODISPLAN_DATA_DIR')
    if defined:
        root = Path(defined).expanduser().resolve()
    elif os.name == 'nt':
        root = Path(os.getenv('PROGRAMDATA', str(Path.home()))) / 'Codisplan' / 'Nfse'
    else:
        root = Path.home() / '.local' / 'share' / 'codisplan-nfse'
    root.mkdir(parents=True, exist_ok=True)
    try:
        root.chmod(0o700)
    except OSError:
        pass
    return root


ROOT = data_root()
DB_PATH = ROOT / 'data.sqlite3'
HOST = os.getenv('CODISPLAN_HOST', '127.0.0.1')
PORT = int(os.getenv('CODISPLAN_PORT', '8765'))
ADN_PRODUCTION = 'https://adn.nfse.gov.br/contribuintes'
ADN_RESTRICTED = 'https://adn.producaorestrita.nfse.gov.br/contribuintes'
MAX_XML_BYTES = 15 * 1024 * 1024
MAX_BATCHES = 50
