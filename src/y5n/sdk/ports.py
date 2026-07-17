"""Port access — communicate with runtime services.

Usage:
    from y5n.sdk import ports

    # Provide a service (setup phase)
    ports.provide("hello", {"greet": lambda n: f"Hello, {n}!"})
    ports.publish("shared", svc)
    ports.promote("global", svc)

    # Consume (run phase)
    hello = ports.get("hello")
    print(hello.greet(name="Yakoon"))          # sync
    print(await hello.greet(name="Yakoon"))     # async
"""

import asyncio
import uuid

from y5n.base.runtime.bus import get_bus
from y5n.base.runtime.context import Call, Response, invoke
from y5n.base.runtime.messages import Placement, RegisterProvider

from .context import current as _current_context


def _has_running_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


class _PortProxy:
    def __init__(self, port_name: str):
        self._port = port_name

    def __getattr__(self, name: str):

        def _build_call(**kwargs) -> Call:
            ctx = _current_context()
            return Call(
                port=self._port,
                method=name,
                args=kwargs,
                caller_path=ctx.node.get("path", ""),
            )

        def _do_call(call: Call) -> Response:
            return invoke(call)

        if _has_running_loop():
            async def async_caller(**kwargs):
                loop = asyncio.get_running_loop()
                call = _build_call(**kwargs)
                response = await loop.run_in_executor(None, _do_call, call)
                if response.error:
                    raise RuntimeError(response.error)
                return response.result

            return async_caller
        else:
            def sync_caller(**kwargs):
                call = _build_call(**kwargs)
                response = _do_call(call)
                if response.error:
                    raise RuntimeError(response.error)
                return response.result

            return sync_caller


def _register(
    name: str,
    service: dict,
    placement: Placement,
) -> None:
    ctx = _current_context()
    provider_id = f"provider:{uuid.uuid4().hex}"
    get_bus().dispatch(
        RegisterProvider(
            provider_id=provider_id,
            exports={name: list(service.keys())},
            service=service,
            placement=placement,
            caller_path=ctx.node.get("path", ""),
        )
    )


def provide(name: str, service: dict) -> None:
    """Provide a service in the current subtree."""
    _register(name, service, Placement.SELF)


def publish(name: str, service: dict) -> None:
    """Publish a service one level up (parent scope)."""
    _register(name, service, Placement.PARENT)


def promote(name: str, service: dict) -> None:
    """Promote a service system-wide (root scope)."""
    _register(name, service, Placement.ROOT)


def get(name: str):
    """Get a port proxy by name."""
    return _PortProxy(name)
