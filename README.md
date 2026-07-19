# SDK — Command Capabilities

The Python SDK is the first-class interface for writing Yakoon commands.

```python
from y5n.sdk import context, models, ports, runtime
```

## Modules

| Module | Import | Purpose |
|--------|--------|---------|
| `context` | `from y5n.sdk import context` | Read-only snapshot of the current invocation |
| `runtime` | `from y5n.sdk import runtime` | Send actions (output, navigation, delay) back to the host |
| `models` | `from y5n.sdk.models import Document, …` | Typed YDS document builder (generated from `spec/yds/yds-v1.yaml`) |
| `ports` | `from y5n.sdk import ports` | Service / port access (provide + consume) |

## Context — Read the World

```python
from y5n.sdk import context

req = context.request()       # parsed invocation arguments
ctx = context.current()       # cwd, workspace, user, session
sess = context.session()      # session-scoped data
```

## Runtime — Act on the World

```python
from y5n.sdk import runtime

await runtime.write("hello")                    # plain text output
await runtime.write({"key": "structured"})      # dict output
await runtime.write(doc)                        # YdsModel → auto to_dict()
await runtime.write(Document(…))                # YDS document

await runtime.error("something went wrong")

await runtime.delay(2.5)                        # sleep seconds
await runtime.delay_until(1234567890.0)         # sleep until timestamp

await runtime.view(clear=True)                  # clear & replace view
await runtime.cwd("/usr/bin")                   # change working directory
```

Every `runtime.*` call is an **awaitable** that yields a `Marker` back to the host's
direct-drive loop. The host never sees SDK types — only plain `dict` / `str` values.

## Models — Typed YDS Documents

Generated from `spec/yds/yds-v1.yaml` via `sdk/python/generate.sh`.

```python
from y5n.sdk.models import Document, Header, Paragraph, InlineText

doc = Document(
    header=Header(title="Hello"),
    blocks=[
        Paragraph(text=[InlineText(text="World")]),
    ],
)
await runtime.write(doc)   # auto-converts via .to_dict()
```

Every model class is a `@dataclass(slots=True, kw_only=True)` that inherits from
`YdsModel` and provides `.to_dict()`. Fields with `None` values are omitted from
the serialized output. The `type` discriminator is set automatically for block and
inline types.

### Generated classes

| Category | Classes |
|----------|---------|
| **Root** | `Document` |
| **Header** | `Header` |
| **Block (base)** | `Block` (subclass for container type hints) |
| **Blocks** | `Text`, `Paragraph`, `Heading`, `Pre`, `Rule`, `Spacer`, `List`, `ListItem`, `Kv`, `KvItem`, `Table`, `Fields`, `Actions`, `Section`, `Stack`, `Flow`, `Collapsible`, `Image` |
| **Inline (base)** | `Inline` (subclass for container type hints) |
| **Inlines** | `InlineText`, `InlineStrong`, `InlineEm`, `InlineUnderline`, `InlineCode`, `InlineLink`, `InlineCmd`, `InlineArg`, `InlineMark`, `InlineSelect`, `InlineSpace`, `InlineBreak` |
| **Standalone** | `TableColumn`, `Field`, `Action` |

## Architecture

```text
Command                       Host
  │                            │
  ├─ context.current() ────────┤  (data snapshot, no call)
  │                            │
  ├─ await runtime.write(doc) ─┤
  │                           │
  │  YdsModel.to_dict() ──────┤  (SDK serializes to plain dict)
  │                           │
  │  Marker(WRITE, dict) ─────┤  (yielded via __await__)
  │                           │
  │                           └─ handler → Outcome
  │
  └─ [done] ── StopIteration ──┘
```

The host drives the command coroutine via `coro.send(None)` — no `create_task`,
no Queue, no polling. Every `await runtime.*` yields a `Marker` that the host
dispatches to a registered handler (producing a DSL Outcome) or processes as a
side effect (e.g. `CWD`).

## Generator

```bash
cd sdk/python
./generate.sh
```

This reads `spec/yds/yds-v1.yaml` and writes `sdk/python/src/y5n/sdk/models.py`.
The generator lives in `sdk/gen/` and supports multiple language targets.

## Rules

- The Host never imports SDK types — it receives plain `dict` / `str`.
- The SDK never imports Host types — it yields `Marker` instances.
- Models are generated, never hand-edited. Extensions go in companion modules.
