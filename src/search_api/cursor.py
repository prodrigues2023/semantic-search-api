"""Opaque pagination cursor, bound to the exact query/filters/profile that
produced it (ADR-0006). A cursor whose hash does not match the request that
presents it is a client error, never a silent restart.
"""
import base64
import hashlib
import json


class CursorMismatchError(ValueError):
    pass


def _request_hash(query: str, filters: list[dict], profile: str) -> str:
    payload = json.dumps(
        {"query": query, "filters": filters, "profile": profile},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def encode_cursor(offset: int, query: str, filters: list[dict], profile: str) -> str:
    body = {"offset": offset, "hash": _request_hash(query, filters, profile)}
    raw = json.dumps(body, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor: str, query: str, filters: list[dict], profile: str) -> int:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        body = json.loads(raw)
        offset = int(body["offset"])
        cursor_hash = body["hash"]
    except Exception as exc:
        raise CursorMismatchError("malformed cursor") from exc

    if cursor_hash != _request_hash(query, filters, profile):
        raise CursorMismatchError(
            "cursor does not match this query, filters, and profile"
        )
    return offset
