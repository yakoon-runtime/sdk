"""Command context — access request, session, path.

Usage:
    from y5n.sdk import context
    ctx = context.current()
    print(ctx.path)
    print(ctx["session"])

    req = context.request()
    name = req.arg(0)
"""

from y5n.base.runtime.context import CommandContext
from y5n.base.runtime.context import context as _ctx


def current() -> CommandContext:
    """Return the current command context."""
    return _ctx.current()


def request():
    """Return a Request object parsed from the current context.

    Provides arg(), option(), has_option() etc.
    """
    return _ctx.request()


__all__ = ["CommandContext", "current", "request"]
