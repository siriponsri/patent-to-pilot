"""Loopback-only network guard used by the smoke command and tests (G01-A12).

While active, any socket connection to a non-loopback address raises ``RemoteCallBlocked``. The workbench core
never imports provider or model-download code; this guard proves it at the socket boundary during a run.
"""
from __future__ import annotations

from contextlib import contextmanager
import ipaddress
import socket

LOOPBACK_NAMES = {"localhost", "127.0.0.1", "::1"}


class RemoteCallBlocked(RuntimeError):
    pass


def _is_loopback(address) -> bool:
    host = address[0] if isinstance(address, tuple) else address
    if isinstance(host, (bytes, bytearray)):
        host = host.decode()
    if host in LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


@contextmanager
def loopback_only(attempts: list | None = None):
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create = socket.create_connection

    def check(address):
        if not _is_loopback(address):
            if attempts is not None:
                attempts.append(repr(address))
            raise RemoteCallBlocked(f"remote network access blocked during G01 run: {address!r}")

    def connect(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6):
            check(address)
        return original_connect(self, address)

    def connect_ex(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6):
            check(address)
        return original_connect_ex(self, address)

    def create_connection(address, *args, **kwargs):
        check(address)
        return original_create(address, *args, **kwargs)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.create_connection = create_connection
    try:
        yield
    finally:
        socket.socket.connect = original_connect
        socket.socket.connect_ex = original_connect_ex
        socket.create_connection = original_create
