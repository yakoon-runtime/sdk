"""Port access — communicate with runtime services.

Usage:
    from y5n.sdk import ports

    hello = ports.get("hello")
    print(hello.greet(name="World"))
"""

from y5n.base.runtime.context import context


class _PortProxy:
    def __init__(self, methods: dict):
        self._methods = methods

    def __getattr__(self, name: str):
        fn = self._methods.get(name)
        if fn is None:
            raise AttributeError(f"port has no method '{name}'")
        return fn


def get(name: str):
    """Get a port proxy by name."""
    ctx = context.current()
    if ctx.ports and name in ctx.ports:
        return _PortProxy(ctx.ports[name])
    raise KeyError(f"port '{name}' not available")
