"""In-process transport — calls the Runtime Bus directly.

Only available when running inside Yakoon's Python process.
"""

from typing import Any


def invoke(call_dict: dict[str, Any]) -> dict[str, Any]:
    from y5n.base.runtime.context import Call as _RuntimeCall
    from y5n.base.runtime.context import invoke as _runtime_invoke

    rc = _RuntimeCall(
        port=call_dict.get("port", ""),
        method=call_dict.get("method", ""),
        args=call_dict.get("args", {}),
        caller_path=call_dict.get("caller_path", ""),
    )
    rr = _runtime_invoke(rc)
    return {"result": rr.result, "error": rr.error}


def register(reg_dict: dict[str, Any]) -> None:
    import uuid

    from y5n.base.runtime.bus import get_bus
    from y5n.base.runtime.messages import Placement, RegisterProvider

    placement = {
        "self": Placement.SELF,
        "parent": Placement.PARENT,
        "root": Placement.ROOT,
    }.get(reg_dict.get("placement", "self"), Placement.SELF)

    get_bus().dispatch(
        RegisterProvider(
            provider_id=f"provider:{uuid.uuid4().hex}",
            exports={reg_dict["name"]: list(reg_dict.get("service", {}).keys())},
            service=reg_dict.get("service"),
            placement=placement,
            caller_path=reg_dict.get("caller_path", ""),
        )
    )
