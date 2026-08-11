"""Store factory (ADR-18, ADR-19): `sdk.store.get()` binds a store client.

Without a name: one declared store → that store; several declared stores
→ error; no declared store → an unbound client. With a name: the client
binds directly — the runtime routes the name to the store the
installation built for it.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.runtime.context import set_context
from y5n.sdk import store


@pytest.mark.parametrize(
    "declared, expected",
    [
        ([], None),
        (["crm"], "crm"),
    ],
)
def test_store_without_name_resolves_default_or_single(declared, expected):
    set_context({"node": {"path": "/crm/sync", "stores": declared}})
    try:
        client = store.get()
        assert client._name == expected
    finally:
        set_context({})


def test_store_without_name_raises_on_multiple():
    set_context({"node": {"path": "/crm/sync", "stores": ["crm", "telemetry"]}})
    try:
        with pytest.raises(ValueError, match="Multiple stores declared"):
            store.get()
    finally:
        set_context({})


def test_store_with_name_uses_it():
    set_context({"node": {"path": "/crm/sync", "stores": ["crm", "telemetry"]}})
    try:
        client = store.get("telemetry")
        assert client._name == "telemetry"
    finally:
        set_context({})


def test_store_with_name_binds_directly():
    """ADR-19: a named client binds directly — the runtime routes it,
    regardless of the ambient caller's declared stores."""
    set_context({"node": {"path": "/crm/sync", "stores": ["crm"]}})
    try:
        client = store.get("telemetry")
        assert client._name == "telemetry"
    finally:
        set_context({})
