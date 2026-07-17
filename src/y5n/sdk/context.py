"""Command execution context.

A frozen snapshot of the call's starting conditions, set once
by the Host (from JSON over stdin/env) and never modified.

Usage:
    from y5n.sdk import context

    ctx = context.current()
    print(ctx.node["path"])
    print(ctx.user["name"])
    print(ctx.tokens)
"""

from contextvars import ContextVar

from .libs import ipc as _ipc
from .libs.models import Context as _Context

_var: ContextVar[_Context] = ContextVar("y5n_sdk_context")
_initialized: bool = False


def _init() -> None:
    """Initialize context from Host-provided JSON (YAK_CONTEXT or YAK_CONTEXT_FILE)."""
    global _initialized
    data = _ipc.read_context()
    if data:
        _var.set(_Context.from_dict(data))
    _initialized = True


def _set(ctx: _Context) -> None:
    """Set the current context (called by the Host)."""
    global _initialized
    _var.set(ctx)
    _initialized = True


def current() -> _Context:
    """Return the current execution context."""
    global _initialized
    if not _initialized:
        _init()
    try:
        return _var.get()
    except LookupError:
        return _Context()


__all__ = ["current"]
