"""Store — the runtime-provided Event Store (ADR-17).

Usage:

    from y5n.sdk import store

    client = store.StoreClient()
    await client.replace(key=box_key(...), doc={...})
    await client.record(key=..., doc={"kind": "read"})

The store belongs to the runtime, not the pack. Every write carries
context and audit automatically — a command never passes an audit flag.

Two layers:
- ``StoreClient`` — typed facade over the shared store; keys travel as
  ``Key`` objects, results come back as ``GetResult``/``PutResult``.
- the module-level functions below — RPC-safe primitives (string keys,
  dict results) used by ``StoreClient`` and available for direct use.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.store.event.models import GetResult, PutResult

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


def _call(method: str, **args: Any):
    ctx = _current_context()
    call = Call(
        port="store",
        method=method,
        args=args,
        caller_path=ctx.node.get("path", ""),
        caller_session_key=ctx.session.get("key", ""),
    )
    return _do_call(call)


# --------------------------------
# RPC-safe primitives
# --------------------------------


async def get(key: str, at_time: str | None = None) -> dict:
    return await _call("get", key=key, at_time=at_time)


async def get_many(keys: list[str]) -> list[dict]:
    return await _call("get_many", keys=keys)


async def history(key: str) -> list[dict]:
    """Return the revisions of an entity — the history, not current state."""
    return await _call("history", key=key)


async def append(
    key: str,
    patch: list[dict] | dict,
    indexes: list[dict] | None = None,
    expected_rev: int | None = None,
) -> dict:
    return await _call(
        "append",
        key=key,
        patch=patch,
        indexes=indexes,
        expected_rev=expected_rev,
    )


async def replace(
    key: str,
    doc: dict,
    indexes: list[dict] | None = None,
    expected_rev: int | None = None,
) -> dict:
    return await _call(
        "replace",
        key=key,
        doc=doc,
        indexes=indexes,
        expected_rev=expected_rev,
    )


async def record(
    key: str,
    doc: dict,
    expected_rev: int | None = None,
    context: dict | None = None,
) -> dict:
    return await _call(
        "record",
        key=key,
        doc=doc,
        expected_rev=expected_rev,
        context=context,
    )


async def delete(key: str, expected_rev: int | None = None) -> dict:
    return await _call("delete", key=key, expected_rev=expected_rev)


async def scan(
    namespace: str,
    index_key: str,
    value: str | int | float | bool | None = None,
    lo: str | int | float | bool | None = None,
    hi: str | int | float | bool | None = None,
    limit: int = 100,
    prefix: str | None = None,
    cursor: str | None = None,
) -> dict:
    return await _call(
        "scan",
        namespace=namespace,
        index_key=index_key,
        value=value,
        lo=lo,
        hi=hi,
        limit=limit,
        prefix=prefix,
        cursor=cursor,
    )


async def ensure_indexes(namespace: str, specs: list[dict]) -> None:
    return await _call("ensure_indexes", namespace=namespace, specs=specs)


async def query_index(
    namespace: str,
    terms: list[dict],
    mode: str = "and",
    limit: int = 100,
) -> dict:
    return await _call(
        "query_index",
        namespace=namespace,
        terms=terms,
        mode=mode,
        limit=limit,
    )


async def next_id(prefix: str) -> str:
    return await _call("next_id", prefix=prefix)


# --------------------------------
# Typed facade
# --------------------------------


def _parse_key(raw: str) -> Key:
    return Key.from_str(raw)


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
    """Typed facade over the runtime's shared Event Store."""

    async def get(self, *, key: Key, at_time=None) -> GetResult:
        result = await get(key=str(key), at_time=at_time)
        if result is None:
            return GetResult(
                key=key,
                entity_id=key.id,
                data=None,
                rev=None,
                as_of=datetime.min,
                historical=False,
            )
        return _get_result(result)

    async def get_many(self, *, keys) -> list[GetResult]:
        results = await get_many(keys=[str(k) for k in keys])
        return [_get_result(r) for r in results]

    async def history(self, *, key: Key) -> list[dict]:
        return await history(key=str(key))

    async def append(
        self,
        *,
        key: Key,
        patch,
        indexes=(),
        expected_rev=None,
    ) -> PutResult:
        result = await append(
            key=str(key),
            patch=patch,
            indexes=_terms(indexes),
            expected_rev=expected_rev,
        )
        return _put_result(result)

    async def replace(
        self,
        *,
        key: Key,
        doc,
        indexes=(),
        expected_rev=None,
    ) -> PutResult:
        result = await replace(
            key=str(key),
            doc=doc,
            indexes=_terms(indexes),
            expected_rev=expected_rev,
        )
        return _put_result(result)

    async def record(
        self,
        *,
        key: Key,
        doc,
        expected_rev=None,
        context=None,
    ) -> PutResult:
        result = await record(
            key=str(key),
            doc=doc,
            expected_rev=expected_rev,
            context=context,
        )
        return _put_result(result)

    async def delete(self, *, key: Key, expected_rev=None) -> PutResult:
        result = await delete(key=str(key), expected_rev=expected_rev)
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
    ) -> list[GetResult]:
        page = await scan(
            namespace=namespace.to_str(),
            index_key=str(index_key),
            value=value,
            lo=lo,
            hi=hi,
            limit=limit,
            prefix=prefix,
            cursor=cursor,
        )
        keys = [_parse_key(k) for k in page["keys"]]
        return await self.get_many(keys=keys)

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
        )

    async def next_id(self, prefix: str) -> str:
        return await next_id(prefix=prefix)


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
]
