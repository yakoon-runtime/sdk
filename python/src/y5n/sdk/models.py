# -----------------------------------------------------------------------------
#  GENERATED FILE
#
#  This file was generated from spec/yds/yds-v1.yaml.
#  DO NOT EDIT — changes will be overwritten.
# -----------------------------------------------------------------------------

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any


class YdsModel:
    __slots__ = ()

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for f in dataclasses.fields(self):  # type: ignore[arg-type]
            value = getattr(self, f.name)
            if value is None:
                continue
            if isinstance(value, YdsModel):
                result[f.name] = value.to_dict()
            elif isinstance(value, list):
                if not value:
                    continue
                result[f.name] = [
                    item.to_dict() if isinstance(item, YdsModel) else item
                    for item in value
                ]
            else:
                result[f.name] = value
        return result

@dataclass(slots=True, kw_only=True)
class Block(YdsModel):
    id: str | None = None

@dataclass(slots=True, kw_only=True)
class Text(Block):
    """A run of rich inline text."""
    text: list[Inline] = field(default_factory=list)
    style: str | None = None
    type: str = 'text'

@dataclass(slots=True, kw_only=True)
class Paragraph(Block):
    """A paragraph of inline text."""
    text: list[Inline] = field(default_factory=list)
    type: str = 'paragraph'

@dataclass(slots=True, kw_only=True)
class Heading(Block):
    """A section heading."""
    level: int = 1
    text: list[Inline] = field(default_factory=list)
    type: str = 'heading'

@dataclass(slots=True, kw_only=True)
class Pre(Block):
    """Preformatted / code block."""
    code: str
    language: str | None = None
    type: str = 'pre'

@dataclass(slots=True, kw_only=True)
class Rule(Block):
    """A horizontal rule."""
    style: str = 'normal'
    type: str = 'rule'

@dataclass(slots=True, kw_only=True)
class Spacer(Block):
    """Vertical spacing."""
    size: int = 1
    type: str = 'spacer'

@dataclass(slots=True, kw_only=True)
class List(Block):
    """An ordered or unordered list."""
    items: list[ListItem] = field(default_factory=list)
    type: str = 'list'

@dataclass(slots=True, kw_only=True)
class ListItem(Block):
    """A single list item."""
    text: list[Inline] = field(default_factory=list)
    blocks: list[Block] = field(default_factory=list)
    type: str = 'list_item'

@dataclass(slots=True, kw_only=True)
class Kv(Block):
    """A key-value listing (property sheet)."""
    items: list[KvItem] = field(default_factory=list)
    type: str = 'kv'

@dataclass(slots=True, kw_only=True)
class KvItem(Block):
    """A single key-value pair."""
    key: str
    value: list[Inline] = field(default_factory=list)
    type: str = 'kv_item'

@dataclass(slots=True, kw_only=True)
class Table(Block):
    """A data table."""
    columns: list[TableColumn] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    variant: str | None = None
    selectable: bool = True
    type: str = 'table'

@dataclass(slots=True, kw_only=True)
class Fields(Block):
    """A group of input fields (form)."""
    name: str | None = None
    fields: list[Field] = field(default_factory=list)
    type: str = 'fields'

@dataclass(slots=True, kw_only=True)
class Actions(Block):
    """A group of action buttons."""
    actions: list[Action] = field(default_factory=list)
    type: str = 'actions'

@dataclass(slots=True, kw_only=True)
class Section(Block):
    """A generic section container."""
    blocks: list[Block] = field(default_factory=list)
    type: str = 'section'

@dataclass(slots=True, kw_only=True)
class Stack(Block):
    """A vertical stack container."""
    blocks: list[Block] = field(default_factory=list)
    type: str = 'stack'

@dataclass(slots=True, kw_only=True)
class Flow(Block):
    """A horizontal flow container."""
    blocks: list[Block] = field(default_factory=list)
    type: str = 'flow'

@dataclass(slots=True, kw_only=True)
class Collapsible(Block):
    """A collapsible section."""
    title: list[Inline] = field(default_factory=list)
    expanded: bool = False
    blocks: list[Block] = field(default_factory=list)
    type: str = 'collapsible'

@dataclass(slots=True, kw_only=True)
class Image(Block):
    """An embedded image."""
    ref: str
    src: str | None = None
    alt: str | None = None
    type: str = 'image'
@dataclass(slots=True, kw_only=True)
class Inline(YdsModel):
    pass

@dataclass(slots=True, kw_only=True)
class InlineText(Inline):
    text: str
    type: str = 'text'

@dataclass(slots=True, kw_only=True)
class InlineStrong(Inline):
    children: list[Inline] = field(default_factory=list)
    type: str = 'strong'

@dataclass(slots=True, kw_only=True)
class InlineEm(Inline):
    children: list[Inline] = field(default_factory=list)
    type: str = 'em'

@dataclass(slots=True, kw_only=True)
class InlineUnderline(Inline):
    children: list[Inline] = field(default_factory=list)
    type: str = 'underline'

@dataclass(slots=True, kw_only=True)
class InlineCode(Inline):
    children: list[Inline] = field(default_factory=list)
    type: str = 'code'

@dataclass(slots=True, kw_only=True)
class InlineLink(Inline):
    href: str
    children: list[Inline] = field(default_factory=list)
    type: str = 'link'

@dataclass(slots=True, kw_only=True)
class InlineCmd(Inline):
    """A clickable command reference."""
    command: str
    variant: str | None = None
    navigable: bool | None = None
    resolvable: bool | None = None
    contextual: bool | None = None
    children: list[Inline] = field(default_factory=list)
    type: str = 'cmd'

@dataclass(slots=True, kw_only=True)
class InlineArg(Inline):
    """A command argument placeholder."""
    children: list[Inline] = field(default_factory=list)
    type: str = 'arg'

@dataclass(slots=True, kw_only=True)
class InlineMark(Inline):
    """A highlighted / marked span."""
    variant: str | None = None
    children: list[Inline] = field(default_factory=list)
    type: str = 'mark'

@dataclass(slots=True, kw_only=True)
class InlineSelect(Inline):
    """A selected / active value label."""
    value: str
    children: list[Inline] = field(default_factory=list)
    type: str = 'select'

@dataclass(slots=True, kw_only=True)
class InlineSpace(Inline):
    count: int = 1
    type: str = 'space'

@dataclass(slots=True, kw_only=True)
class InlineBreak(Inline):
    count: int = 1
    type: str = 'break'

@dataclass(slots=True, kw_only=True)
class TableColumn(YdsModel):
    """A single column definition."""
    key: str
    title: str

@dataclass(slots=True, kw_only=True)
class Field(YdsModel):
    """A single input field definition."""
    policy: str
    name: str | None = None
    required: bool = False
    title: str | None = None
    hint: str | None = None
    default: str | None = None
    lookup: str | None = None

@dataclass(slots=True, kw_only=True)
class Action(YdsModel):
    """A single action / command button."""
    label: str
    command: str
    scope: str | None = None

@dataclass(slots=True, kw_only=True)
class Header(YdsModel):
    """Document-level presentation metadata."""
    role: str = 'info'
    title: str | None = None
    subtitle: str | None = None
    error_kind: str | None = None
    error_code: str | None = None

@dataclass(slots=True, kw_only=True)
class Document(YdsModel):
    """Root of every YDS document.  Produced by the Compiler and normalised by the Runtime before dispatch."""
    kind: str = 'document'
    header: Header
    blocks: list[Block] = field(default_factory=list)