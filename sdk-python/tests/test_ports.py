"""ports.get — the contract argument is typing information only.

Proves the SDK slice: ``get(name)`` stays the dynamic escape hatch and
``get(name, contract)`` returns the identical runtime proxy; the
contract argument leaves no runtime trace.
"""

from __future__ import annotations

import pytest
from typing import Protocol

from y5n.sdk import ports
from y5n.sdk.ports import _PortProxy, _RemoteCall


class _Greeter(Protocol):
    def greet(self, *, name: str) -> str: ...


def test_get_without_contract_returns_proxy():
    proxy = ports.get("hello")
    assert isinstance(proxy, _PortProxy)
    assert proxy._port == "hello"


def test_get_with_contract_returns_identical_proxy():
    plain = ports.get("ident.auth")
    typed = ports.get("ident.auth", _Greeter)
    assert type(typed) is _PortProxy
    assert vars(typed) == vars(plain) == {"_port": "ident.auth"}


def test_contract_argument_is_not_inspected_or_stored():
    contract = object()
    proxy = ports.get("ident.auth", contract)
    assert vars(proxy) == {"_port": "ident.auth"}


def test_proxy_call_semantics_unchanged_with_contract():
    proxy = ports.get("ident.auth", _Greeter)
    call = proxy.authenticate(username="u", secret="s")
    assert isinstance(call, _RemoteCall)
    assert call._port == "ident.auth"
    assert call._method == "authenticate"
    assert call._kwargs == {"username": "u", "secret": "s"}


def test_proxy_rejects_positional_args_with_contract():
    proxy = ports.get("ident.auth", _Greeter)
    with pytest.raises(TypeError):
        proxy.authenticate("u")
