"""Port access — communicate with runtime services.

Usage:
    from y5n.sdk import ports

    # register a service (Command A)
    ports.register("hello", {"greet": lambda name="World": f"Hello, {name}!"})

    # consume a service (Command B)
    hello = ports.get("hello")
    print(hello.greet(name="Yakoon"))
"""

from y5n.base.runtime.context import _port_registry


class _PortProxy:
    def __init__(self, methods: dict):
        self._methods = methods

    def __getattr__(self, name: str):
        fn = self._methods.get(name)
        if fn is None:
            raise AttributeError(f"port has no method '{name}'")
        return fn


def register(name: str, service: dict) -> None:
    """Register a port service in the runtime.

    The service persists across command invocations.
    """
    _port_registry[name] = service


def get(name: str):
    """Get a port proxy by name."""
    service = _port_registry.get(name)
    if service is None:
        raise KeyError(f"port '{name}' not registered")
    return _PortProxy(service)
