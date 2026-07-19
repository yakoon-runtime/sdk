"""Runtime actions — answers "what should the runtime do?".

Every function returns a custom awaitable that yields a marker
tuple to the host's direct-drive loop:

    ('write', view)        → out(view, mode=...)
    ('error', text)        → out({"kind": "error", "text": text})
    ('delay', seconds)     → delay(seconds)
    ('delay_until', ts)    → delay_until(ts)
    ('view', params)       → view(**params)

Usage:
    from y5n.sdk import runtime

    await runtime.write("hello")
    await runtime.delay(2)
    await runtime.view(clear=True)
"""

from __future__ import annotations

from typing import Any


class _Write:
    __slots__ = ("_view",)

    def __init__(self, view: dict | str) -> None:
        self._view = view

    def __await__(self):
        yield ("write", self._view)


class _Error:
    __slots__ = ("_text",)

    def __init__(self, text: str) -> None:
        self._text = text

    def __await__(self):
        yield ("error", self._text)


class _Delay:
    __slots__ = ("_seconds",)

    def __init__(self, seconds: float) -> None:
        self._seconds = seconds

    def __await__(self):
        yield ("delay", self._seconds)


class _DelayUntil:
    __slots__ = ("_timestamp",)

    def __init__(self, timestamp: float) -> None:
        self._timestamp = timestamp

    def __await__(self):
        yield ("delay_until", self._timestamp)


class _View:
    __slots__ = ("_params",)

    def __init__(self, **params: Any) -> None:
        self._params = params

    def __await__(self):
        yield ("view", self._params)


def write(view: dict | str) -> _Write:
    """Emit output to the client.

    Usage:
        await runtime.write("hello")
        await runtime.write({"kind": "document", ...})
    """
    return _Write(view)


def error(text: str) -> _Error:
    """Emit an error message to the client.

    Usage:
        await runtime.error("something went wrong")
    """
    return _Error(text)


def delay(seconds: float) -> _Delay:
    """Suspend the current invocation for *seconds*.

    Usage:
        await runtime.delay(2)
    """
    return _Delay(seconds)


def delay_until(timestamp: float) -> _DelayUntil:
    """Suspend the current invocation until *timestamp* (Unix).

    Usage:
        await runtime.delay_until(time.time() + 10)
    """
    return _DelayUntil(timestamp)


def view(**params: Any) -> _View:
    """Send a viewport hint to the client.

    Usage:
        await runtime.view(clear=True)
    """
    return _View(**params)


__all__ = ["delay", "delay_until", "error", "view", "write"]
