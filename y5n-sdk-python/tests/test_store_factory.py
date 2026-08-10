"""Store factory (ADR-18): `sdk.store()` resolves the caller's stores.

Without a name: no declared store → default; one declared store → that
store; several declared stores → error. The ambiguity is surfaced at the
API, never resolved implicitly.
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
        client = store()
        assert client._name == expected
    finally:
        set_context({})


def test_store_without_name_raises_on_multiple():
    set_context({"node": {"path": "/crm/sync", "stores": ["crm", "telemetry"]}})
    try:
        with pytest.raises(ValueError, match="Multiple stores declared"):
            store()
    finally:
        set_context({})


def test_store_with_name_uses_it():
    set_context({"node": {"path": "/crm/sync", "stores": ["crm", "telemetry"]}})
    try:
        client = store("telemetry")
        assert client._name == "telemetry"
    finally:
        set_context({})
