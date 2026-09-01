"""Registration scope — provide/publish/promote transmit the caller path.

Proves the registration-scope behavior end to end through the SDK and
the default Runtime Bus: the setup node's path from the invocation
context reaches Register.caller_path, Placement maps it to the scoped
route, and resolution picks the closest visible provider.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.runtime.bus import get_bus
from y5n.runtime.api.runtime.context import set_context
from y5n.sdk import ports


@pytest.fixture(autouse=True)
def _sdk_endpoint(monkeypatch):
    monkeypatch.setenv("YAK_ENDPOINT", "inprocess://")


@pytest.fixture(autouse=True)
def _clear_context():
    set_context({})
    yield
    set_context({})


class _Service:
    def op(self, *, value: str = "") -> str:
        return value


def _register(scope: str, name: str, path: str | None) -> None:
    if path is not None:
        set_context({"node": {"path": path}})
    getattr(ports, scope)(name, _Service())


def _resolve(name: str, caller_path: str) -> str | None:
    return get_bus().resolver.resolve(name, "op", caller_path)


def test_provide_scopes_to_the_setup_node():
    _register("provide", "scope.provide.svc", "/contacts/customer")
    assert _resolve("scope.provide.svc", "/contacts/customer") is not None
    assert _resolve("scope.provide.svc", "/contacts/customer/edit") is not None
    assert _resolve("scope.provide.svc", "/contacts") is None
    assert _resolve("scope.provide.svc", "/worlds") is None


def test_publish_scopes_to_the_parent_node():
    _register("publish", "scope.publish.svc", "/contacts/customer")
    assert _resolve("scope.publish.svc", "/contacts") is not None
    assert _resolve("scope.publish.svc", "/contacts/customer") is not None
    assert _resolve("scope.publish.svc", "/contacts/customer/edit") is not None
    assert _resolve("scope.publish.svc", "/worlds") is None


def test_promote_scopes_to_root():
    _register("promote", "scope.promote.svc", "/contacts/customer")
    assert _resolve("scope.promote.svc", "/") is not None
    assert _resolve("scope.promote.svc", "/worlds") is not None
    assert _resolve("scope.promote.svc", "/contacts/customer") is not None


def test_closest_visible_provider_wins():
    _register("promote", "scope.closest.svc", "/")
    root = _resolve("scope.closest.svc", "/")
    _register("publish", "scope.closest.svc", "/contacts/customer")
    contacts = _resolve("scope.closest.svc", "/contacts")
    _register("provide", "scope.closest.svc", "/contacts/customer")
    customer = _resolve("scope.closest.svc", "/contacts/customer")

    assert len({root, contacts, customer}) == 3
    assert _resolve("scope.closest.svc", "/") == root
    assert _resolve("scope.closest.svc", "/contacts") == contacts
    assert _resolve("scope.closest.svc", "/contacts/customer") == customer
    assert _resolve("scope.closest.svc", "/contacts/customer/edit") == customer
    assert _resolve("scope.closest.svc", "/worlds") == root


def test_no_context_registration_stays_root():
    _register("provide", "scope.nocontext.provide", None)
    _register("publish", "scope.nocontext.publish", None)
    assert _resolve("scope.nocontext.provide", "/worlds") is not None
    assert _resolve("scope.nocontext.publish", "/worlds") is not None
