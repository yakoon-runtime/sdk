"""Port access — communicate with runtime services.

Usage:
    from y5n.sdk import ports

    # Provide a service (setup phase)
    ports.provide("hello", {"greet": lambda n: f"Hello, {n}!"})
    ports.publish("shared", svc)    # one level up
    ports.promote("global", svc)    # system-wide

    # Consume (run phase)
    hello = ports.get("hello")
    print(hello.greet(name="Yakoon"))
"""

import uuid

from y5n.base.runtime.bus import get_bus
from y5n.base.runtime.context import Call, context, invoke
from y5n.base.runtime.messages import Placement, RegisterProvider


class _PortProxy:
    def __init__(self, port_name: str):
        self._port = port_name

    def __getattr__(self, name: str):
        def caller(**kwargs):
            ctx = context.current()
            response = invoke(
                Call(
                    port=self._port,
                    method=name,
                    args=kwargs,
                    caller_path=ctx.path,
                )
            )
            if response.error:
                raise RuntimeError(response.error)
            return response.result

        return caller


def _register(
    name: str,
    service: dict,
    placement: Placement,
) -> None:
    ctx = context.current()
    provider_id = f"provider:{uuid.uuid4().hex}"
    get_bus().dispatch(
        RegisterProvider(
            provider_id=provider_id,
            exports={name: list(service.keys())},
            service=service,
            placement=placement,
            caller_path=ctx.path,
        )
    )


def provide(name: str, service: dict) -> None:
    """Provide a service in the current subtree.

    The service becomes visible to the current node and all
    its children via hierarchical lookup. Siblings and parents
    cannot see it unless they publish or promote it.

    Equivalent to the classic NodePorts.provide():
    a node declares a local capability.

    Resolution: caller walks up from its path toward root.
    A service registered at /a/b is found by callers at /a/b,
    /a/b/c, /a/b/d, etc. — but not by callers at /a or /a/c.
    """
    _register(name, service, Placement.SELF)


def publish(name: str, service: dict) -> None:
    """Publish a service one level up (parent scope).

    The service is registered at the parent of the current node.
    It becomes visible to the parent and every node in the
    parent's subtree (siblings, cousins, etc.).

    Equivalent to the classic NodePorts.publish():
    a node exports a capability into the parent runtime space.

    Example:
        A provider running at /usr/bin/world calls publish().
        The service is registered at /usr/bin and is visible
        to /usr/bin, /usr/bin/world, /usr/bin/ls, etc.
    """
    _register(name, service, Placement.PARENT)


def promote(name: str, service: dict) -> None:
    """Promote a service system-wide (root scope).

    The service is registered at "/" and is visible from
    every node in the tree.

    Equivalent to the classic NodePorts.promote():
    a capability promoted to root is visible regardless of
    tree location — intended for cross-branch services
    like authentication that need global reach.
    """
    _register(name, service, Placement.ROOT)


def get(name: str):
    """Get a port proxy by name.

    Resolution walks the tree upward from the caller's path.
    The closest registration wins.
    """
    return _PortProxy(name)
