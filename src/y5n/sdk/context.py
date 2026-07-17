"""Command execution context.

A frozen snapshot of the call's starting conditions, set once
by the Host and never modified.

Usage:
    from y5n.sdk import context

    ctx = context.current()
    print(ctx.node["path"])
    print(ctx.user["name"])
    print(ctx.tokens)
"""

from contextvars import ContextVar
from typing import Any

from y5n.base.contracts import Context as _Context

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


__all__ = ["current"]
