"""Command execution context.

A frozen snapshot of the call's starting conditions, set once
by the Host and never modified.

Usage:
    from y5n.sdk import context

    ctx = context.current()
    print(ctx.node["path"])
    print(ctx.user["name"])

    req = context.request()
    print(req.arg(0))
    print(req.option("name"))
"""

from contextvars import ContextVar

from .libs.models import Context as _Context
from .libs.models import Request as _Request

_var: ContextVar[_Context] = ContextVar("y5n_sdk_context")


def _set(ctx: _Context) -> None:
    """Set the current context (called by the Host)."""
    _var.set(ctx)


def current() -> _Context:
    """Return the current execution context."""
    try:
        return _var.get()
    except LookupError:
        return _Context()


def request() -> _Request:
    """Return a Request object parsed from the current context tokens."""
    ctx = current()
    return _Request.from_tokens(ctx.tokens)


__all__ = ["current", "request"]
