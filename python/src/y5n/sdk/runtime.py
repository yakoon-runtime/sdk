"""Runtime actions — answers "what should the runtime do?".

Every function returns a custom awaitable whose ``__await__`` yields
a ``Marker`` (see ``y5n.base.host.protocol``) to the host's direct-drive loop.

Usage:
    from y5n.sdk import runtime

    await runtime.write("hello")
    await runtime.delay(2)

    # Domain-style API (new)
    await runtime.io.write("hello")
    await runtime.timer.delay(2)
    flows = await runtime.scheduler.flows()
"""

from __future__ import annotations

from typing import Any

from y5n.base.host.protocol import Marker, MarkerKind
from y5n.sdk.models import YdsModel

# ----- Internal awaitables ---------------------------------------------------


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


class _FlowsList:
    def __await__(self):
        from y5n.sdk.context import flow as _ctx_flow

        exclude_id = _ctx_flow().id
        result = yield Marker(MarkerKind.FLOWS_LIST, exclude_id)
        return result


class _FlowStop:
    __slots__ = ("_flow_id",)

    def __init__(self, flow_id: str) -> None:
        self._flow_id = flow_id

    def __await__(self):
        yield Marker(MarkerKind.FLOW_STOP, self._flow_id)


class _FlowFg:
    __slots__ = ("_flow_id",)

    def __init__(self, flow_id: str) -> None:
        self._flow_id = flow_id

    def __await__(self):
        yield Marker(MarkerKind.FLOW_FG, self._flow_id)


class _FlowBg:
    def __await__(self):
        result = yield Marker(MarkerKind.FLOW_BG, None)
        return result


class _NetworkList:
    def __await__(self):
        from y5n.base.runtime.bus import get_bus
        from y5n.base.runtime.context import Call

        bus = get_bus()
        resp = yield from bus.async_dispatch(
            Call(
                port="source",
                method="read",
                args={"query": "system:runtimes --list"},
                caller_path="",
            )
        ).__await__()
        data = resp.result if hasattr(resp, "result") else resp
        rows = data.rows if hasattr(data, "rows") else []
        return [{"name": r["name"], "url": r["url"]} for r in rows]


# ----- Domain classes ---------------------------------------------------------


class _IO:
    """Input / Output — communication with the user."""

    @staticmethod
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
            ``None`` (default) — let the host decide.
        """
        if isinstance(view, YdsModel):
            view = view.to_dict()  # type: ignore[assignment]
        return _Write(view, mode=mode)

    @staticmethod
    def error(text: str) -> _Error:
        return _Error(text)


class _Timer:
    """Timer — delay and scheduling helpers."""

    @staticmethod
    def delay(seconds: float) -> _Delay:
        return _Delay(seconds)

    @staticmethod
    def delay_until(timestamp: float) -> _DelayUntil:
        return _DelayUntil(timestamp)


class _Scheduler:
    """Scheduler — process / flow management."""

    @staticmethod
    def flows() -> _FlowsList:
        """Return list of active flow dicts for the current session."""
        return _FlowsList()

    @staticmethod
    def stop(flow_id: str) -> _FlowStop:
        """Stop a flow by ID."""
        return _FlowStop(flow_id)

    @staticmethod
    def foreground(flow_id: str) -> _FlowFg:
        """Bring a flow to the foreground."""
        return _FlowFg(flow_id)

    @staticmethod
    def background() -> _FlowBg:
        """Send the current foreground flow to the background."""
        return _FlowBg()


class _Network:
    """Network — remote runtime discovery and connection."""

    @staticmethod
    def list() -> _NetworkList:
        """Return list of known remote runtimes."""
        return _NetworkList()


# ----- Domain instances -------------------------------------------------------

io = _IO()
timer = _Timer()
scheduler = _Scheduler()
network = _Network()

# ----- Flat backward-compat aliases -------------------------------------------


def write(view, *, mode=None):
    return io.write(view, mode=mode)


def error(text: str) -> _Error:
    return io.error(text)


def delay(seconds: float) -> _Delay:
    return timer.delay(seconds)


def delay_until(timestamp: float) -> _DelayUntil:
    return timer.delay_until(timestamp)


def view(**params: Any) -> _View:
    return _View(**params)


def cwd(path: str) -> _Cwd:
    return _Cwd(path)


__all__ = [
    "cwd",
    "delay",
    "delay_until",
    "error",
    "io",
    "network",
    "scheduler",
    "timer",
    "view",
    "write",
]
