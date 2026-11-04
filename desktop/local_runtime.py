"""Local HTTP server owned by the desktop tray app (not a Windows Service)."""
from __future__ import annotations

import socket
import threading
from typing import Callable

import uvicorn


class LocalPortalRuntime:
    """Start/stop FastAPI without elevation, consoles or external SCM processes.

    GUI calls these methods on Tk's thread. Uvicorn executes only in a daemon
    worker; stop requests are cooperative and the bind failure is surfaced via
    the status callback rather than claiming the service has been installed.
    """

    def __init__(self, app_factory: Callable, host: str = '127.0.0.1'):
        if host != '127.0.0.1':
            raise ValueError('A administração local deve usar somente 127.0.0.1.')
        self.app_factory = app_factory
        self.host = host
        self.port = 8765
        self.server: uvicorn.Server | None = None
        self.thread: threading.Thread | None = None
        self.error: str = ''
        self._lock = threading.RLock()

    @property
    def active(self) -> bool:
        with self._lock:
            return bool(self.thread and self.thread.is_alive() and self.server and self.server.started)

    @property
    def running(self) -> bool:
        with self._lock:
            return bool(self.thread and self.thread.is_alive())

    def start(self, port: int = 8765) -> None:
        port = int(port)
        if not 1024 <= port <= 65535:
            raise ValueError('A porta deve estar entre 1024 e 65535.')
        with self._lock:
            if self.thread and self.thread.is_alive():
                if self.port == port:
                    return
                raise RuntimeError('Interrompa o servidor antes de trocar a porta.')
            self.port = port
            self.error = ''
            # A socket owned by another application must not be treated as ours.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
                sock.bind((self.host, port))
            except OSError as exc:
                self.error = f'A porta {port} não está disponível: {exc}'
                raise RuntimeError(self.error) from exc
            finally:
                sock.close()
            app = self.app_factory()
            cfg = uvicorn.Config(app, host=self.host, port=port, log_level='warning', access_log=False, workers=1)
            self.server = uvicorn.Server(cfg)
            self.thread = threading.Thread(target=self._run, daemon=True, name='CodisplanNFSe-HTTP')
            self.thread.start()

    def _run(self):
        try:
            assert self.server is not None
            self.server.run()
        except BaseException as exc:
            self.error = f'Falha ao iniciar o portal: {exc}'
        finally:
            # On clean shutdown, started stays True on some uvicorn versions.
            with self._lock:
                if self.server is not None:
                    self.server.started = False

    def stop(self, timeout: float = 4.0) -> None:
        with self._lock:
            srv, worker = self.server, self.thread
            if srv:
                srv.should_exit = True
        if worker and worker.is_alive() and worker is not threading.current_thread():
            worker.join(timeout)
        with self._lock:
            if worker and worker.is_alive():
                self.error = 'O servidor ainda está encerrando.'
            else:
                self.server = None
                self.thread = None

    def restart(self, port: int | None = None) -> None:
        target = self.port if port is None else port
        self.stop()
        if self.running:
            raise RuntimeError('Não foi possível parar o servidor para reiniciar.')
        self.start(target)
