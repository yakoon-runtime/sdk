"""StoreClient — the shared Event Store through the SDK, typed.

The runtime owns one store; ``sdk.store()`` reaches it over the ``store``
port (RPC-safe: string keys, dict results). Pack services, however, are
written against the store's typed models (``GetResult``, ``PutResult``,
``Key``, ``Namespace``). ``StoreClient`` bridges the two: it calls
``sdk.store()`` and re-constructs the typed objects.

Usage (in pack setup):

    store = StoreClient()

    contacts = ContactService(
        on_get=store.get,
        on_replace=store.replace,
        on_scan=store.scan,
        on_delete=store.delete,
        on_query_index=store.query_index,
        on_next_id=store.next_id,
    )
"""

from __future__ import annotations

from datetime import datetime

from y5n.runtime.api.naming import Key, Namespace
from y5n.runtime.store.event.models import GetResult, PutResult

from . import store as _store


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


class StoreClient:
    """Typed facade over the runtime's shared Event Store."""

    async def get(self, *, key: Key, at_time=None) -> GetResult:
        result = await _store.get(key=str(key), at_time=at_time)
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
        results = await _store.get_many(keys=[str(k) for k in keys])
        return [_get_result(r) for r in results]

    async def append(
        self,
        *,
        key: Key,
        patch,
        indexes=(),
        expected_rev=None,
    ) -> PutResult:
        result = await _store.append(
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
        result = await _store.replace(
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
        result = await _store.record(
            key=str(key),
            doc=doc,
            expected_rev=expected_rev,
            context=context,
        )
        return _put_result(result)

    async def delete(self, *, key: Key, expected_rev=None) -> PutResult:
        result = await _store.delete(key=str(key), expected_rev=expected_rev)
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
        page = await _store.scan(
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
        page = await _store.query_index(
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
        await _store.ensure_indexes(
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
        return await _store.next_id(prefix=prefix)


def _terms(indexes):
    if not indexes:
        return []
    return [{"key": str(t.key), "value": t.value} for t in indexes]
