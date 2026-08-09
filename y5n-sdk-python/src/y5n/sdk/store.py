"""Store — the runtime-provided Event Store (ADR-17).

Usage:

    from y5n.sdk import store

    await store.replace(key="luma/box/global#42", doc={...})
    await store.record(key="system/activity/global#x", doc={"kind": "read"})
    await store.get(key="luma/box/global#42")

The store belongs to the runtime, not the pack. Every write carries
context and audit automatically — a command never passes an audit flag.
"""

from __future__ import annotations

from typing import Any

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


async def get(key: str, at_time: str | None = None) -> dict:
    return await _call("get", key=key, at_time=at_time)


async def get_many(keys: list[str]) -> list[dict]:
    return await _call("get_many", keys=keys)


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


__all__ = [
    "append",
    "delete",
    "ensure_indexes",
    "get",
    "get_many",
    "next_id",
    "query_index",
    "record",
    "replace",
    "scan",
]
