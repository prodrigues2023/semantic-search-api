"""A stub embedder: deterministic, offline, no API key.

This is NOT a real embedding model. It exists so the reference implementation
runs with zero external dependencies (docs/context.md's "no cloud account"
requirement). Swapping it for a real model (OpenAI, Cohere, sentence-
transformers) means implementing `embed(text) -> list[float]` -- the contract
and the fusion logic behind it do not change, which is the whole point of
ADR-0002.

The technique is feature hashing over a small synonym-expanded token set:
each token is mapped to a canonical group (so "declined" and "failing" hash
to the same bucket), then hashed into a fixed-width vector and L2-normalised.
It is good enough to demonstrate that hybrid ranking fuses two genuinely
different signals -- it is not a substitute for a trained model's grasp of
meaning.
"""
import hashlib
import math
import re

from .config import EMBEDDING_DIM

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Small, hand-written synonym groups covering the sample corpus. This is the
# toy stand-in for a model's learned semantics -- see the module docstring.
_SYNONYM_GROUPS = [
    {"failing", "fail", "failed", "declined", "decline", "reject", "rejected"},
    {"payment", "payments", "transaction", "transactions", "charge", "charges", "billing"},
    {"refund", "refunds", "reimbursement", "reimburse", "chargeback"},
    {"error", "errors", "issue", "issues", "problem", "problems"},
    {"contract", "contracts", "agreement", "agreements", "terms"},
    {"collision", "collisions", "conflict", "conflicts", "duplicate", "duplicates"},
    {"retry", "retries", "retried", "automatic", "automatically"},
]

_CANONICAL = {}
for _group in _SYNONYM_GROUPS:
    _root = sorted(_group)[0]
    for _tok in _group:
        _CANONICAL[_tok] = _root


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _canonical(token: str) -> str:
    return _CANONICAL.get(token, token)


def embed(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIM
    for token in _tokens(text):
        canon = _canonical(token)
        digest = hashlib.md5(canon.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % EMBEDDING_DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0.0:
        return vector
    return [v / norm for v in vector]
