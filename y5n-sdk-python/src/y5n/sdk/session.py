"""Session — the SDK domain for the runtime's session capability.

The runtime keeps the live Session state (identity, language, session
data). ``session`` is the stable, typed developer API over the generic
``session`` port — like ``store`` is the typed API over the ``store``
port. The port name and the transport never leak into the command.

Usage:

    from y5n.sdk import session

    current = await session.current()
    user = current.user or ""
    await session.update(patch={"data": {"luma.current_world": world.id}})
    await session.attach(target_key=other_key)

Layer model:

- ``session`` — the SDK domain (this module): typed methods, context
  injection, models.
- the ``session`` port — the generic runtime ABI this domain calls.
- ``ports`` — the escape hatch for arbitrary capabilities (e.g. a
  pack-provided ``ident.auth``); first-class capabilities like session
  get a domain, not raw port access.
"""

from __future__ import annotations

from typing import Any

from .context import current as _current_context
from .libs import transport as _transport
from .libs.models import Call, Response
from .libs.models import Session as SessionModel


async def _invoke(call: Call) -> Response:
    result = await _transport.invoke(call.to_dict())
    if isinstance(result, dict):
        return Response.from_dict(result)
    return Response(result=result)


async def _do_call(call: Call):
    response = await _invoke(call)
    if response.error:
        raise RuntimeError(response.error)
    return response.result


def _call(method: str, **args: Any):
    ctx = _current_context()
    call = Call(
        port="session",
        method=method,
        args=args,
        caller_path=ctx.node.get("path", ""),
        caller_session_key=ctx.session.get("key", ""),
    )
    return _do_call(call)


class Session:
    """Typed facade over the runtime's session capability.

    Every call carries the caller's context automatically; a command
    never passes a session key.
    """

    async def current(self) -> SessionModel:
        """Return the live session of the caller."""
        data = await _call("current")
        return SessionModel.from_context(
            {
                "key": data.get("key"),
                "lang": data.get("lang"),
                "data": data.get("data", {}),
            },
            {"id": data.get("user_id"), "name": data.get("user_name")},
        )

    async def list(self) -> list[dict]:
        """Enumerate the live sessions of this runtime."""
        return await _call("list")

    async def attach(self, *, target_key: str) -> None:
        """Attach the caller's session to another live session."""
        await _call("attach", target_key=target_key)

    async def detach(self) -> None:
        """Detach the caller's session."""
        await _call("detach")

    async def logout(self) -> None:
        """Log the caller's session out."""
        await _call("logout")

    async def update(self, *, patch: dict[str, Any]) -> dict[str, Any]:
        """Update the caller's session data.

        Returns ``{"applied": {...}, "ignored": {...}}`` describing which
        patch keys were honored.
        """
        return await _call("update", patch=patch)

    async def set_permissions(self, *, specs: list[str]) -> dict[str, int]:
        """Set the caller's permissions from serializable spec strings.

        The ident pack resolves an account's effective permissions into
        spec strings (e.g. ``"/crm/contact/edit|rwx"``); the runtime
        parses them into its internal permission set.
        """
        return await _call("set_permissions", specs=specs)


session = Session()


__all__ = ["Session", "session"]
