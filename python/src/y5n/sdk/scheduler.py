from __future__ import annotations

from y5n.base.host.protocol import Marker, MarkerKind


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


class _Scheduler:
    def flows(self) -> _FlowsList:
        return _FlowsList()

    def stop(self, flow_id: str) -> _FlowStop:
        return _FlowStop(flow_id)

    def foreground(self, flow_id: str) -> _FlowFg:
        return _FlowFg(flow_id)

    def background(self) -> _FlowBg:
        return _FlowBg()


scheduler = _Scheduler()


__all__ = ["scheduler"]
