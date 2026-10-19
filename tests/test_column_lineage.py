"""Column lineage tests (SQLGlot)."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlglot")

from pyairflowtester.column_lineage import analyze_dbt_model, analyze_sql


def test_select_columns_map_to_sources():
    lineage = analyze_sql(
        "SELECT o.id AS order_id, o.total * 1.2 AS gross, c.name "
        "FROM orders o JOIN customers c ON c.id = o.customer_id"
    )
    assert lineage.outputs["order_id"] == ["o.id"]
    assert lineage.outputs["gross"] == ["o.total"]
    assert lineage.outputs["name"] == ["c.name"]
    assert set(lineage.sources) == {"c", "o"}


def test_wildcard_is_explicitly_unknown():
    lineage = analyze_sql("SELECT * FROM orders")
    assert lineage.outputs["*"] == []
    assert any("wildcard" in warning for warning in lineage.warnings)


def test_dbt_model_uses_compiled_code():
    lineage = analyze_dbt_model(
        {"compiled_code": "SELECT id AS user_id FROM users", "raw_code": "ignored"}
    )
    assert lineage.outputs == {"user_id": ["id"]}


def test_cte_columns_resolve_to_source_tables():
    lineage = analyze_sql(
        "WITH base AS (SELECT id, total FROM raw.orders) "
        "SELECT b.id AS order_id, b.total * 2 AS gross FROM base b"
    )
    assert lineage.outputs["order_id"] == ["raw.orders.id"]
    assert lineage.outputs["gross"] == ["raw.orders.total"]
    assert "raw.orders" not in lineage.outputs["order_id"]
