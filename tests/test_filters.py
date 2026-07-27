import pytest

from search_api.filters import InvalidFilterError, build_filter_clause


def test_empty_filters_is_true():
    sql, params = build_filter_clause([])
    assert sql == "TRUE"
    assert params == {}


def test_eq_filter_binds_field_and_value_as_params():
    sql, params = build_filter_clause([{"field": "category", "op": "eq", "value": "billing"}])
    assert "metadata ->>" in sql
    assert params["f_field_0"] == "category"
    assert params["f_value_0"] == "billing"


def test_in_filter_requires_list():
    with pytest.raises(InvalidFilterError):
        build_filter_clause([{"field": "category", "op": "in", "value": "billing"}])


def test_unsupported_operator_rejected():
    with pytest.raises(InvalidFilterError):
        build_filter_clause([{"field": "category", "op": "ne", "value": "billing"}])


def test_multiple_filters_anded():
    sql, _ = build_filter_clause(
        [
            {"field": "category", "op": "eq", "value": "billing"},
            {"field": "tenant", "op": "eq", "value": "acme"},
        ]
    )
    assert " AND " in sql
