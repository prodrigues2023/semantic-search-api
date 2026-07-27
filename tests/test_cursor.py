import pytest

from search_api.cursor import CursorMismatchError, decode_cursor, encode_cursor


def test_roundtrip():
    c = encode_cursor(10, "refund", [], "hybrid")
    assert decode_cursor(c, "refund", [], "hybrid") == 10


def test_mismatched_query_rejected():
    c = encode_cursor(10, "refund", [], "hybrid")
    with pytest.raises(CursorMismatchError):
        decode_cursor(c, "different query", [], "hybrid")


def test_mismatched_filters_rejected():
    c = encode_cursor(0, "refund", [{"field": "category", "op": "eq", "value": "billing"}], "hybrid")
    with pytest.raises(CursorMismatchError):
        decode_cursor(c, "refund", [], "hybrid")


def test_mismatched_profile_rejected():
    c = encode_cursor(0, "refund", [], "hybrid")
    with pytest.raises(CursorMismatchError):
        decode_cursor(c, "refund", [], "lexical")


def test_malformed_cursor_rejected():
    with pytest.raises(CursorMismatchError):
        decode_cursor("not-a-real-cursor!!", "refund", [], "hybrid")
