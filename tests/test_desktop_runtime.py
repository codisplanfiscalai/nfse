"""Contract tests for the portable, non-admin, tray-owned HTTP runtime."""
from __future__ import annotations

import socket
import time
from urllib.request import urlopen

import pytest
from fastapi import FastAPI

from desktop.local_runtime import LocalPortalRuntime


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def app_factory():
    app = FastAPI()

    @app.get('/health/ready')
    def ready():
        return {'status': 'ready'}

    return app


def test_starts_on_localhost_without_windows_service():
    port = free_port()
    runtime = LocalPortalRuntime(app_factory)
    try:
        runtime.start(port)
        deadline = time.monotonic() + 6
        while not runtime.active and time.monotonic() < deadline:
            time.sleep(0.04)
        assert runtime.active and runtime.port == port
        with urlopen(f'http://127.0.0.1:{port}/health/ready', timeout=2) as reply:
            assert reply.status == 200
        runtime.start(port)  # Idempotent while already running.
    finally:
        runtime.stop()
    assert not runtime.running


def test_runtime_can_restart_on_new_port():
    port = free_port()
    other = free_port()
    runtime = LocalPortalRuntime(app_factory)
    try:
        runtime.start(port)
        runtime.restart(other)
        deadline = time.monotonic() + 5
        while not runtime.active and time.monotonic() < deadline:
            time.sleep(0.04)
        assert runtime.active and runtime.port == other
    finally:
        runtime.stop()


def test_occupied_port_is_rejected_not_assumed_ours():
    port = free_port()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', port))
        s.listen()
        runtime = LocalPortalRuntime(app_factory)
        with pytest.raises(RuntimeError, match='não está disponível'):
            runtime.start(port)
        assert not runtime.running


def test_rejects_external_host():
    with pytest.raises(ValueError):
        LocalPortalRuntime(app_factory, host='0.0.0.0')
