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
from y5n.sdk.models import YdsModel


class _Write:
    __slots__ = ("_view", "_mode")

    def __init__(self, view: dict | str, mode: str | None = None) -> None:
        self._view = view
        self._mode = mode

    def __await__(self):
        value: Any = (self._view, self._mode) if self._mode else self._view
        yield Marker(MarkerKind.WRITE, value)


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


class _Cwd:
    __slots__ = ("_path",)

    def __init__(self, path: str) -> None:
        self._path = path

    def __await__(self):
        yield Marker(MarkerKind.CWD, self._path)


def write(
    view: YdsModel | dict | str,
    *,
    mode: str | None = None,
) -> _Write:
    """Write output to the client.

    Parameters
    ----------
    mode:
        ``"replace"`` — replace the current view.
        ``"append"`` — append to the current view.
        ``None`` (default) — let the host decide (first call→replace, rest→append).
    """
    if isinstance(view, YdsModel):
        view = view.to_dict()  # type: ignore[assignment]
    return _Write(view, mode=mode)


def error(text: str) -> _Error:
    return _Error(text)


def delay(seconds: float) -> _Delay:
    return _Delay(seconds)


def delay_until(timestamp: float) -> _DelayUntil:
    return _DelayUntil(timestamp)


def view(**params: Any) -> _View:
    return _View(**params)


def cwd(path: str) -> _Cwd:
    """Change the current working directory.

    Usage:
        await runtime.cwd("/usr/bin")
    """
    return _Cwd(path)


__all__ = ["cwd", "delay", "delay_until", "error", "view", "write"]
