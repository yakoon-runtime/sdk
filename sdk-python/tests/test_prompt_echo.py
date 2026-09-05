from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.primitives import AwaitEvent
from y5n.runtime.api.runtime.input import InputContext
from y5n.sdk import io
from y5n.sdk.io import prompt as module_prompt

VIEW = {"kind": "document", "header": {"role": "info", "title": ""}, "blocks": []}


def _run(awaitable, reply="typed"):
    gen = awaitable.__await__()
    pulse = gen.send(None)
    try:
        gen.send(reply)
    except StopIteration as stop:
        return pulse, stop.value
    raise AssertionError("prompt did not return")


def _view_effect(pulse):
    return [e for e in pulse.effects if hasattr(e, "view")][0]


def test_prompt_default_inherits_context():
    pulse, result = _run(io.prompt(VIEW))

    effect = _view_effect(pulse)
    assert effect.view == VIEW
    assert effect.persist is True
    assert effect.ctx is None
    assert isinstance(pulse.control, AwaitEvent)
    assert pulse.control.channel == "__user__"
    assert pulse.control.scope is Scope.USER_INPUT
    assert result == "typed"


def test_prompt_without_echo_carries_echo_free_context():
    pulse, result = _run(io.prompt(VIEW, echo=False))

    effect = _view_effect(pulse)
    assert isinstance(effect.ctx, InputContext)
    assert effect.ctx.echo is None
    assert result == "typed"


def test_module_prompt_passes_echo_through():
    pulse, _ = _run(module_prompt(VIEW, echo=False))

    assert _view_effect(pulse).ctx.echo is None

    pulse, _ = _run(module_prompt(VIEW))
    assert _view_effect(pulse).ctx is None


def test_prompt_accepts_string_projection_in_both_modes():
    pulse, result = _run(io.prompt("Your name:", echo=False))
    assert _view_effect(pulse).ctx.echo is None
    assert result == "typed"

    pulse, result = _run(io.prompt("Your name:"))
    assert _view_effect(pulse).ctx is None
    assert result == "typed"
