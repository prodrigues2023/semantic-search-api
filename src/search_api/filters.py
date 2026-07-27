"""Translate the filter grammar (docs/filter-grammar.md) into SQL.

Filters are pushed into both the lexical and semantic retrieval queries
before the top-k is taken (ADR-0004) -- this module is what makes that true:
callers of `build_filter_clause` get one WHERE fragment they attach to
either query, never a post-filter applied to results.
"""
from sqlalchemy import text

_OPS = {"eq", "in", "gte", "lte"}


class InvalidFilterError(ValueError):
    pass


def build_filter_clause(filters: list[dict], param_prefix: str = "f"):
    """Return (sql_fragment, params) ANDing every condition.

    The field name is passed as a bind parameter to the `->>` operator, not
    spliced into the SQL as an identifier, so there is no injection surface
    regardless of what the caller sends as `field`.
    """
    if not filters:
        return "TRUE", {}

    clauses = []
    params = {}
    for i, cond in enumerate(filters):
        field = cond["field"]
        op = cond["op"]
        value = cond["value"]
        if op not in _OPS:
            raise InvalidFilterError(f"unsupported operator: {op}")

        field_key = f"{param_prefix}_field_{i}"
        params[field_key] = field

        if op == "eq":
            value_key = f"{param_prefix}_value_{i}"
            params[value_key] = str(value)
            clauses.append(f"(metadata ->> :{field_key}) = :{value_key}")
        elif op == "in":
            if not isinstance(value, list):
                raise InvalidFilterError("'in' requires a list value")
            value_key = f"{param_prefix}_value_{i}"
            params[value_key] = [str(v) for v in value]
            clauses.append(f"(metadata ->> :{field_key}) = ANY(:{value_key})")
        elif op in ("gte", "lte"):
            value_key = f"{param_prefix}_value_{i}"
            params[value_key] = float(value)
            operator = ">=" if op == "gte" else "<="
            clauses.append(f"(metadata ->> :{field_key})::numeric {operator} :{value_key}")

    return " AND ".join(clauses), params


def filter_clause_sql(filters: list[dict], param_prefix: str = "f"):
    sql, params = build_filter_clause(filters, param_prefix)
    return text(sql).bindparams(**params) if params else text(sql)
