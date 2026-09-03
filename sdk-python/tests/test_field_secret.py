"""Field.secret — the generic renderer-independent secret-input contract.

Field is the renderer-visible input-field vocabulary; ``secret`` marks
presentation semantics (non-echoed input) and must survive the SDK →
Param → structured projection path unchanged. Ordinary fields carry no
secret semantics.
"""

from __future__ import annotations

from y5n.sdk import io
from y5n.sdk.models import Field


def test_field_secret_serialization():
    plain = Field(key="user", policy="text").to_dict()
    assert plain["secret"] is False

    secret = Field(key="password", policy="text", secret=True).to_dict()
    assert secret["secret"] is True


def test_field_secret_roundtrip():
    field = Field(key="password", policy="text", secret=True)
    assert Field.from_dict(field.to_dict()).secret is True


def _first_field_entry(pulse) -> dict:
    view = pulse.effects[1].view
    return view["blocks"][0]["blocks"][0]["fields"][0]


def test_form_renders_secret_field_entry():
    gen = io.form(
        [{"key": "password", "title": "Password", "required": True, "secret": True}],
        title="Login",
    ).__await__()
    pulse = gen.send(None)

    entry = _first_field_entry(pulse)
    assert entry["name"] == "password"
    assert entry["state"] == "active"
    assert entry["secret"] is True


def test_ordinary_field_has_no_secret_semantics():
    gen = io.form(
        [{"key": "user", "title": "User"}],
        title="Login",
    ).__await__()
    pulse = gen.send(None)

    entry = _first_field_entry(pulse)
    assert entry["name"] == "user"
    assert "secret" not in entry
