"""Port access — communicate with runtime services.

Usage:
    from y5n.sdk import ports

    ports.provide("hello", {"greet": lambda n: f"Hello, {n}!"})
    ports.publish("shared", svc)
    ports.promote("global", svc)

    hello = ports.get("hello")
    print(hello.greet(name="Yakoon"))
    print(await hello.greet(name="Yakoon"))
"""

import asyncio

from .context import current as _current_context
from .libs import ipc as _ipc
from .libs.models import Call, Register, Response


def _invoke(call: Call) -> Response:
    result = _ipc.invoke(call.to_dict())
    if isinstance(result, dict):
        return Response.from_dict(result)
    return Response(result=result)


def _register(reg: Register) -> None:
    _ipc.register(reg.to_dict())


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
                loop = asyncio.get_running_loop()
                call = _build_call(**kwargs)
                return await loop.run_in_executor(None, _do_call, call)

            return async_caller
        else:

            def sync_caller(**kwargs):
                call = _build_call(**kwargs)
                return _do_call(call)

            return sync_caller


def provide(name: str, service: dict) -> None:
    _register(Register(name=name, service=service, placement="self"))


def publish(name: str, service: dict) -> None:
    _register(Register(name=name, service=service, placement="parent"))


def promote(name: str, service: dict) -> None:
    _register(Register(name=name, service=service, placement="root"))


def get(name: str):
    return _PortProxy(name)
