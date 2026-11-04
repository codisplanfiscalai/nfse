"""Application data and runtime configuration; never commit secrets."""
from __future__ import annotations
import os
from pathlib import Path
import sys


def data_directory() -> Path:
    configured = os.environ.get("NFSE_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    if sys.platform == "win32":
        return Path(os.getenv("PROGRAMDATA", Path.home())) / "Codisplan" / "NFSe"
    return Path.home() / ".local" / "share" / "codisplan-nfse"


def root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


def bundled(path: str) -> Path:
    return root() / path


def ensure_data_dir() -> Path:
    folder = data_directory()
    folder.mkdir(parents=True, exist_ok=True)
    if sys.platform != 'win32':
        folder.chmod(0o700)
    return folder


def version() -> str:
    if os.getenv('NFSE_VERSION'):
        return os.environ['NFSE_VERSION']
    packaged = bundled('src/nfse/distribution.json')
    if packaged.exists():
        try:
            import json
            return str(json.loads(packaged.read_text(encoding='utf-8'))['version'])
        except (ValueError, KeyError, OSError):
            pass
    path = bundled('VERSION')
    return path.read_text(encoding='utf-8').strip() if path.exists() else '0.2.0'
