"""Store — the runtime-provided Event Store (ADR-17).

Usage:

    from y5n.sdk import store

    client = store()
    await client.replace(key=box_key(...), doc={...})
    await client.record(key=..., doc={"kind": "read"})

The store belongs to the runtime, not the pack. Every write carries
context and audit automatically — a command never passes an audit flag.
A pack only ever says "I need persistence"; the runtime decides how it is
provided. ``store()`` returns the shared store client; later the same call
may accept a profile (``store(profile="telemetry")``) without the pack
changing.

Two layers:
- ``store()`` — the stable public entry point, returns a ``StoreClient``.
- ``StoreClient`` — the typed facade over the shared store; keys travel as
  ``Key`` objects, results come back as ``GetResult``/``PutResult``.
- the module-level functions below — RPC-safe primitives (string keys,
  dict results) used by ``StoreClient`` and available for direct use.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.store.event.models import EntityId, GetResult, PutResult

from .context import current as _current_context
from .libs import transport as _transport
from .libs.models import Call, Response


async def _invoke(call: Call) -> Response:
    result = await _transport.invoke(call.to_dict())
    if isinstance(result, dict):
        return Response.from_dict(result)
    return Response(result=result)


async def _do_call(call: Call):
    response = await _invoke(call)
    if response.error:
        raise RuntimeError(response.error)
    return response.result


def _call(method: str, store_name: str | None = None, **args: Any):
    ctx = _current_context()
    call = Call(
        port="store",
        method=method,
        args=args,
        caller_path=ctx.node.get("path", ""),
        caller_session_key=ctx.session.get("key", ""),
        store_name=store_name,
    )
    return _do_call(call)


# --------------------------------
# RPC-safe primitives
# --------------------------------


async def get(
    key: dict, at_time: str | None = None, store_name: str | None = None
) -> dict:
    return await _call("get", store_name=store_name, key=key, at_time=at_time)


async def get_many(keys: list[dict], store_name: str | None = None) -> list[dict]:
    return await _call("get_many", store_name=store_name, keys=keys)


async def history(key: dict, store_name: str | None = None) -> list[dict]:
    """Return the revisions of an entity — the history, not current state."""
    return await _call("history", store_name=store_name, key=key)


async def append(
    key: dict,
    patch: list[dict] | dict,
    indexes: list[dict] | None = None,
    snapshot_hint: str | None = None,
    meta: dict | None = None,
    expected_rev: int | None = None,
    store_name: str | None = None,
) -> dict:
    return await _call(
        "append",
        store_name=store_name,
        key=key,
        patch=patch,
        indexes=indexes,
        snapshot_hint=snapshot_hint,
        meta=meta,
        expected_rev=expected_rev,
    )


async def replace(
    key: dict,
    doc: dict,
    indexes: list[dict] | None = None,
    snapshot_hint: str | None = None,
    expected_rev: int | None = None,
    store_name: str | None = None,
) -> dict:
    return await _call(
        "replace",
        store_name=store_name,
        key=key,
        doc=doc,
        indexes=indexes,
        snapshot_hint=snapshot_hint,
        expected_rev=expected_rev,
    )


async def record(
    key: dict,
    doc: dict,
    expected_rev: int | None = None,
    context: dict | None = None,
    indexes: list[dict] | None = None,
    store_name: str | None = None,
) -> dict:
    return await _call(
        "record",
        store_name=store_name,
        key=key,
        doc=doc,
        expected_rev=expected_rev,
        context=context,
        indexes=indexes,
    )


async def delete(
    key: dict,
    meta: dict | None = None,
    expected_rev: int | None = None,
    store_name: str | None = None,
) -> dict:
    return await _call(
        "delete",
        store_name=store_name,
        key=key,
        meta=meta,
        expected_rev=expected_rev,
    )


async def scan(
    namespace: str,
    index_key: str,
    value: str | int | float | bool | None = None,
    lo: str | int | float | bool | None = None,
    hi: str | int | float | bool | None = None,
    limit: int = 100,
    prefix: str | None = None,
    cursor: str | None = None,
    store_name: str | None = None,
) -> dict:
    return await _call(
        "scan",
        store_name=store_name,
        namespace=namespace,
        index_key=index_key,
        value=value,
        lo=lo,
        hi=hi,
        limit=limit,
        prefix=prefix,
        cursor=cursor,
    )


async def ensure_indexes(
    namespace: str, specs: list[dict], store_name: str | None = None
) -> None:
    return await _call(
        "ensure_indexes", store_name=store_name, namespace=namespace, specs=specs
    )


async def query_index(
    namespace: str,
    terms: list[dict],
    mode: str = "and",
    limit: int = 100,
    store_name: str | None = None,
) -> dict:
    return await _call(
        "query_index",
        store_name=store_name,
        namespace=namespace,
        terms=terms,
        mode=mode,
        limit=limit,
    )


async def next_id(prefix: str, store_name: str | None = None) -> str:
    return await _call("next_id", store_name=store_name, prefix=prefix)


# --------------------------------
# Typed facade
# --------------------------------


def _parse_key(raw: dict) -> Key:
    ns = raw.get("namespace") or {}
    return Key(
        namespace=Namespace(
            domain=ns.get("domain") or "",
            kind=ns.get("kind") or "",
            space=ns.get("space", "global") or "global",
        ),
        id=raw.get("id", ""),
    )


def _key_to_dict(key: Key) -> dict:
    return {
        "namespace": {
            "domain": key.namespace.domain,
            "kind": key.namespace.kind,
            "space": key.namespace.space,
        },
        "id": key.id,
    }


def _parse_ns(raw: str) -> Namespace:
    domain, kind, space = raw.split("/")
    return Namespace(domain, kind, space)


def _get_result(d: dict) -> GetResult:
    return GetResult(
        key=_parse_key(d["key"]),
        entity_id=d["entity_id"],
        data=d["data"],
        rev=d["rev"],
        as_of=datetime.fromisoformat(d["as_of"]) if d["as_of"] else datetime.min,
        historical=d["historical"],
    )


def _put_result(d: dict) -> PutResult:
    return PutResult(
        entity_id=d["entity_id"],
        rev=d["rev"],
        updated_at=(
            datetime.fromisoformat(d["updated_at"]) if d["updated_at"] else datetime.min
        ),
        snapshot_written=d["snapshot_written"],
    )


def _terms(indexes):
    if not indexes:
        return []
    return [{"key": str(t.key), "value": t.value} for t in indexes]


class StoreClient:
    """Typed facade over a logical store (ADR-18).

    ``name`` is the logical store this client is bound to (``crm``,
    ``telemetry``) — a name the pack declared, never infrastructure. When
    ``None``, the runtime resolves the caller's first declared store.
    """

    def __init__(self, name: str | None = None) -> None:
        self._name = name

    async def get(self, *, key: Key, at_time=None) -> GetResult:
        result = await get(
            key=_key_to_dict(key), at_time=at_time, store_name=self._name
        )
        if result is None:
            return GetResult(
                key=key,
                entity_id=EntityId(key.id),
                data=None,
                rev=None,
                as_of=datetime.min,
                historical=False,
            )
        return _get_result(result)

    async def get_many(self, *, keys) -> list[GetResult]:
        results = await get_many(
            keys=[_key_to_dict(k) for k in keys], store_name=self._name
        )
        return [_get_result(r) for r in results]

    async def history(self, *, key: Key) -> list[dict]:
        return await history(key=_key_to_dict(key), store_name=self._name)

    async def append(
        self,
        *,
        key: Key,
        patch,
        indexes=(),
        snapshot_hint=None,
        meta=None,
        expected_rev=None,
    ) -> PutResult:
        result = await append(
            key=_key_to_dict(key),
            patch=patch,
            indexes=_terms(indexes),
            snapshot_hint=snapshot_hint,
            meta=meta,
            expected_rev=expected_rev,
            store_name=self._name,
        )
        return _put_result(result)

    async def replace(
        self,
        *,
        key: Key,
        doc,
        indexes=(),
        snapshot_hint=None,
        expected_rev=None,
    ) -> PutResult:
        result = await replace(
            key=_key_to_dict(key),
            doc=doc,
            indexes=_terms(indexes),
            snapshot_hint=snapshot_hint,
            expected_rev=expected_rev,
            store_name=self._name,
        )
        return _put_result(result)

    async def record(
        self,
        *,
        key: Key,
        doc,
        expected_rev=None,
        context=None,
        indexes=(),
    ) -> PutResult:
        result = await record(
            key=_key_to_dict(key),
            doc=doc,
            expected_rev=expected_rev,
            context=context,
            indexes=_terms(indexes),
            store_name=self._name,
        )
        return _put_result(result)

    async def delete(self, *, key: Key, meta=None, expected_rev=None) -> PutResult:
        result = await delete(
            key=_key_to_dict(key),
            meta=meta,
            expected_rev=expected_rev,
            store_name=self._name,
        )
        return _put_result(result)

    async def scan(
        self,
        *,
        namespace: Namespace,
        index_key,
        value=None,
        lo=None,
        hi=None,
        limit=100,
        prefix=None,
        cursor=None,
    ) -> tuple[list[Key], str | None]:
        page = await scan(
            namespace=namespace.to_str(),
            index_key=str(index_key),
            value=value,
            lo=lo,
            hi=hi,
            limit=limit,
            prefix=prefix,
            cursor=cursor,
            store_name=self._name,
        )
        keys = [_parse_key(k) for k in page["keys"]]
        return keys, page.get("cursor")

    async def query_index(
        self,
        *,
        namespace: Namespace,
        terms,
        mode="and",
        limit=100,
    ) -> list[Key]:
        page = await query_index(
            namespace=namespace.to_str(),
            terms=[
                {"index_key": str(t.index_key), "op": t.op, "value": t.value}
                for t in terms
            ],
            mode=mode,
            limit=limit,
            store_name=self._name,
        )
        return [_parse_key(k) for k in page["keys"]]

    async def ensure_indexes(self, *, namespace: Namespace, specs) -> None:
        await ensure_indexes(
            namespace=namespace.to_str(),
            specs=[
                {
                    "key": str(s.key),
                    "value_type": s.value_type.value,
                    "unique": s.unique,
                }
                for s in specs
            ],
            store_name=self._name,
        )

    async def next_id(self, prefix: str) -> str:
        return await next_id(prefix=prefix, store_name=self._name)


def store(name: str | None = None) -> StoreClient:
    """Return a client for a logical store (ADR-18, ADR-19).

    The stable public entry point. ``name`` is a logical store the pack
    declared (``store("crm")``) — never infrastructure.

    Without a name, the caller's declared stores decide:

    - no stores declared → the default store;
    - exactly one declared store → that store;
    - several declared stores → error, the ambiguity must be resolved.

    With a name, the store must be declared: an undeclared dependency is
    an error, like an import whose module is not in the requirements
    (ADR-19). The resolution happens here, at the API — neither an
    ambiguous nor an undeclared call travels through the bus.
    """
    declared = list(_current_context().node.get("stores") or [])
    if name is None:
        if len(declared) > 1:
            raise ValueError("Multiple stores declared. Please specify a store name.")
        name = declared[0] if declared else None
    elif name not in declared:
        raise ValueError(
            f"Undeclared store '{name}'. Add it to the pack's stores: declaration."
        )
    return StoreClient(name=name)


__all__ = [
    "StoreClient",
    "append",
    "delete",
    "ensure_indexes",
    "get",
    "get_many",
    "history",
    "next_id",
    "query_index",
    "record",
    "replace",
    "scan",
    "store",
]
