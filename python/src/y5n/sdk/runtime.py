"""Runtime actions — answers "what should the runtime do?".

Every function returns a custom awaitable whose ``__await__`` yields
a ``Marker`` (see ``y5n.base.host.protocol``) to the host's direct-drive loop.

Usage:
    from y5n.sdk import runtime

    await runtime.write("hello")
    await runtime.delay(2)
    await runtime.view(clear=True)
"""

from __future__ import annotations

from typing import Any

from y5n.base.host.protocol import Marker, MarkerKind


class _Write:
    __slots__ = ("_view",)

    def __init__(self, view: dict | str) -> None:
        self._view = view

    def __await__(self):
        yield Marker(MarkerKind.WRITE, self._view)


class _Error:
    __slots__ = ("_text",)

    def __init__(self, text: str) -> None:
        self._text = text

    def __await__(self):
        yield Marker(MarkerKind.ERROR, self._text)


class _Delay:
    __slots__ = ("_seconds",)

    def __init__(self, seconds: float) -> None:
        self._seconds = seconds

    def __await__(self):
        yield Marker(MarkerKind.DELAY, self._seconds)


class _DelayUntil:
    __slots__ = ("_timestamp",)

    def __init__(self, timestamp: float) -> None:
        self._timestamp = timestamp

    def __await__(self):
        yield Marker(MarkerKind.DELAY_UNTIL, self._timestamp)


class _View:
    __slots__ = ("_params",)

    def __init__(self, **params: Any) -> None:
        self._params = params

    def __await__(self):
        yield Marker(MarkerKind.VIEW, self._params)


def write(view: dict | str) -> _Write:
    return _Write(view)


def error(text: str) -> _Error:
    return _Error(text)


def delay(seconds: float) -> _Delay:
    return _Delay(seconds)


def delay_until(timestamp: float) -> _DelayUntil:
    return _DelayUntil(timestamp)


def view(**params: Any) -> _View:
    return _View(**params)


__all__ = ["delay", "delay_until", "error", "view", "write"]
