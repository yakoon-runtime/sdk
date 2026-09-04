"""io.form elements mode — mixed YDS presentation blocks and Fields.

Slice 2 of the Option-B evolution: the SDK forwards ``elements=`` to the
runtime Form. Real SDK models project with inline-list text (the YDF
shape the Shell renderer consumes); ``fields=``/``title``/``intro``
remain fully compatible.
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.runtime import Event
from y5n.sdk import io
from y5n.sdk.models import Field, Heading, InlineText, Rule, Text


def _drive(awaitable, inputs: list) -> tuple[list, dict]:
    gen = awaitable
    pulses: list = []
    try:
        pulse = gen.send(None)
        while True:
            pulses.append(pulse)
            control = getattr(pulse, "control", None)
            if control is not None and getattr(control, "channel", None) == "__user__":
                pulse = gen.send(Event(payload=inputs.pop(0)))
            else:
                pulse = gen.send(None)
    except StopIteration as stop:
        return pulses, stop.value


def _views(pulses: list) -> list[dict]:
    return [e.view for p in pulses for e in p.effects if hasattr(e, "view")]


def _field_entries(view: dict) -> list[dict]:
    entries = []
    for block in view["blocks"]:
        if block["type"] == "fields":
            entries.extend(block["fields"])
    return entries


def _sign_in():
    return io.form(
        elements=[
            Heading(text=[InlineText(text="SIGN IN")]),
            Rule(),
            Text(text=[InlineText(text="Authenticate to continue.")]),
            Field(key="user", title="Username"),
            Field(key="password", title="Password", secret=True),
        ]
    ).__await__()


def test_elements_forwarding_projects_mixed_blocks():
    _pulses, _values = None, None
    gen = _sign_in()
    pulse = gen.send(None)
    view = pulse.effects[1].view

    assert [b["type"] for b in view["blocks"]] == [
        "heading",
        "rule",
        "text",
        "fields",
    ]
    # SDK models project with inline-list text — the shape inlines.render
    # and the Shell renderer consume
    assert view["blocks"][0] == {
        "type": "heading",
        "level": 1,
        "text": [{"type": "text", "text": "SIGN IN"}],
    }
    assert view["blocks"][2] == {
        "type": "text",
        "text": [{"type": "text", "text": "Authenticate to continue."}],
    }

    entries = _field_entries(view)
    assert [f["name"] for f in entries] == ["user", "password"]
    assert entries[0]["state"] == "active"
    assert entries[0].get("secret") is not True
    assert entries[1]["state"] == "idle"
    assert entries[1]["secret"] is True
    assert view["header"] == {"role": "info", "title": ""}


def test_elements_values_contain_only_fields():
    pulses, values = _drive(_sign_in(), inputs=["stefan", "hunter2"])

    assert values == {"user": "stefan", "password": "hunter2"}

    final = _field_entries(_views(pulses)[-1])
    assert [f["state"] for f in final] == ["done", "done"]
    assert final[1]["value"] == "hunter2"  # secret field keeps its raw value


def test_fields_mode_remains_unchanged():
    gen = io.form(
        [{"key": "password", "title": "Password", "required": True, "secret": True}],
        title="Login",
    ).__await__()
    pulse = gen.send(None)
    view = pulse.effects[1].view

    assert view["header"] == {"role": "info", "title": "Login"}
    section = view["blocks"][0]
    assert section["type"] == "section"
    node = section["blocks"][0]
    assert node["type"] == "fields"
    assert node["name"] == "Login"
    assert node["fields"][0]["name"] == "password"
    assert node["fields"][0]["secret"] is True


def test_elements_and_fields_are_mutually_exclusive():
    with pytest.raises(ValueError):
        io.form(
            fields=[{"key": "a"}],
            elements=[Rule()],
        ).__await__().send(None)


def test_elements_reject_title_and_intro():
    with pytest.raises(ValueError):
        io.form(elements=[Rule()], title="T").__await__().send(None)
    with pytest.raises(ValueError):
        io.form(
            elements=[Rule()],
            intro="I",
        ).__await__().send(None)
