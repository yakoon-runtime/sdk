"""Runtime — backward-compatible facade for all domain modules.

Prefer importing domain modules directly:

    from y5n.sdk import io, timer, scheduler, network, viewport
"""

from __future__ import annotations

from y5n.base.host.protocol import Marker, MarkerKind

from .io import io
from .timer import timer
from .scheduler import scheduler
from .network import network
from .viewport import viewport


class _Cwd:
    __slots__ = ("_path",)

    def __init__(self, path: str) -> None:
        self._path = path

    def __await__(self):
        yield Marker(MarkerKind.CWD, self._path)


def cwd(path: str) -> _Cwd:
    return _Cwd(path)


__all__ = [
    "cwd",
    "io",
    "network",
    "scheduler",
    "timer",
    "viewport",
]
