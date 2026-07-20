from __future__ import annotations


class _SessionList:
    def __await__(self):
        from y5n.base.runtime.bus import get_bus
        from y5n.base.runtime.context import Call

        bus = get_bus()
        resp = yield from bus.async_dispatch(
            Call(
                port="source",
                method="read",
                args={"query": "system:sessions --list"},
                caller_path="",
            )
        ).__await__()
        data = resp.result if hasattr(resp, "result") else resp
        rows = data.rows if hasattr(data, "rows") else []
        return rows


class _Session:
    def list(self) -> _SessionList:
        return _SessionList()


session = _Session()


__all__ = ["session"]
