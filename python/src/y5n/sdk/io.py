from __future__ import annotations

from y5n.runtime.engine.host.protocol import Marker, MarkerKind
from y5n.sdk.models import YdsModel


class _Write:
    __slots__ = ("_view", "_mode")

    def __init__(self, view: dict | str, mode: str | None = None) -> None:
        self._view = view
        self._mode = mode

    def __await__(self):
        value: object = (self._view, self._mode) if self._mode else self._view
        yield Marker(MarkerKind.WRITE, value)


class _Error:
    __slots__ = ("_text",)

    def __init__(self, text: str) -> None:
        self._text = text

    def __await__(self):
        yield Marker(MarkerKind.ERROR, self._text)


class _IO:
    def write(
        self,
        view: YdsModel | dict | str,
        *,
        mode: str | None = None,
    ) -> _Write:
        if isinstance(view, YdsModel):
            view = view.to_dict()
        return _Write(view, mode=mode)

    def error(self, text: str) -> _Error:
        return _Error(text)


io = _IO()


def write(view, *, mode=None):
    return io.write(view, mode=mode)


def error(text: str) -> _Error:
    return io.error(text)


__all__ = ["error", "io", "write"]
