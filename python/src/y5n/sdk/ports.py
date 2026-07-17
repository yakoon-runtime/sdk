"""Port access — communicate with runtime services.

Usage:
    from y5n.sdk import ports

    class Greeter:
        def greet(self, name="World"):
            return f"Hello, {name}!"

    ports.promote("hello", Greeter())

    hello = ports.get("hello")
    print(hello.greet(name="Yakoon"))
    print(await hello.greet(name="Yakoon"))
"""

import asyncio
from typing import Any

from .context import current as _current_context
from .libs import transport as _transport
from .libs.models import Call, Register, Response


def _extract_methods(service: object) -> dict[str, Any]:
    return {
        name: getattr(service, name)
        for name in dir(service)
        if not name.startswith("_") and callable(getattr(service, name))
    }


def _invoke(call: Call) -> Response:
    result = _transport.invoke(call.to_dict())
    if isinstance(result, dict):
        return Response.from_dict(result)
    return Response(result=result)


def _register(reg: Register, callables: dict[str, Any] | None = None) -> None:
    _transport.register(reg.to_dict(), callables)


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

        def _do_call(call: Call):
            response = _invoke(call)
            if response.error:
                raise RuntimeError(response.error)
            return response.result

        if _has_running_loop():

            async def async_caller(**kwargs):
                call = _build_call(**kwargs)
                return _do_call(call)

            return async_caller
        else:

            def sync_caller(**kwargs):
                call = _build_call(**kwargs)
                return _do_call(call)

            return sync_caller


def provide(name: str, service: object) -> None:
    callables = _extract_methods(service)
    _register(
        Register(name=name, methods=list(callables), placement="self"),
        callables,
    )


def publish(name: str, service: object) -> None:
    callables = _extract_methods(service)
    _register(
        Register(name=name, methods=list(callables), placement="parent"),
        callables,
    )


def promote(name: str, service: object) -> None:
    callables = _extract_methods(service)
    _register(
        Register(name=name, methods=list(callables), placement="root"),
        callables,
    )


def get(name: str):
    return _PortProxy(name)
