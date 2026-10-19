"""Column-level SQL lineage with SQLGlot.

Used to complement table-level DAG/dbt graphs: for each projected output
column, report the source columns it reads. Unsupported/dynamic SQL degrades to
an explicit warning rather than a guessed edge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


class LineageUnavailable(RuntimeError):
    """Raised when sqlglot is not installed."""


@dataclass
class ColumnLineage:
    dialect: str
    outputs: dict[str, list[str]] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dialect": self.dialect,
            "outputs": self.outputs,
            "sources": self.sources,
            "warnings": self.warnings,
        }


def _require_sqlglot():
    try:
        import sqlglot
        from sqlglot import exp
    except ImportError as exc:
        raise LineageUnavailable(
            "sqlglot is required for column lineage. Install with "
            '`pip install "pyairflowtester[lineage]"`.'
        ) from exc
    return sqlglot, exp


def _cte_maps(statement, exp) -> dict[str, dict[str, list[str]]]:
    maps: dict[str, dict[str, list[str]]] = {}
    for cte in statement.find_all(exp.CTE):
        select = cte.this.find(exp.Select) if cte.this is not None else None
        if select is None:
            continue
        base_tables = [t.sql() for t in select.find_all(exp.Table)]
        base = base_tables[0] if base_tables else ""
        mapping: dict[str, list[str]] = {}
        for projection in select.expressions:
            output = projection.alias_or_name
            if output:
                columns = []
                for column in projection.find_all(exp.Column):
                    columns.append(
                        f"{base}.{column.name}" if base and not column.table else column.sql()
                    )
                mapping[output] = columns
        maps[cte.alias_or_name] = mapping
    return maps


def analyze_sql(sql: str, *, dialect: Optional[str] = None) -> ColumnLineage:
    """Extract output-column -> source-column references from one SELECT."""
    sqlglot, exp = _require_sqlglot()
    parsed = sqlglot.parse(sql, read=dialect)
    result = ColumnLineage(dialect=dialect or "default")

    for statement in parsed:
        if statement is None:
            continue
        select = statement.find(exp.Select)
        if select is None:
            result.warnings.append("statement is not a SELECT; skipped")
            continue
        cte_maps = _cte_maps(statement, exp)
        alias_to_cte = {
            table.alias_or_name: table.name
            for table in select.find_all(exp.Table)
            if table.name in cte_maps
        }
        for table in select.find_all(exp.Table):
            name = table.name
            alias = table.alias
            result.sources.append(alias or name)
        for projection in select.expressions:
            output = projection.alias_or_name
            if not output:
                result.warnings.append("projection without an output name; skipped")
                continue
            resolved = []
            for column in projection.find_all(exp.Column):
                table = alias_to_cte.get(column.table, column.table)
                if table in cte_maps and column.name in cte_maps[table]:
                    for source in cte_maps[table][column.name]:
                        # CTE source columns are raw table.column strings.
                        resolved.append(source)
                else:
                    resolved.append(column.sql(dialect=dialect))
            result.outputs[output] = sorted(set(resolved))
            if not resolved and projection.find(exp.Star):
                result.warnings.append(f"{output}: wildcard projection has unknown columns")
    result.sources = sorted(set(result.sources))
    return result


def analyze_file(path: str | Path, *, dialect: Optional[str] = None) -> ColumnLineage:
    return analyze_sql(Path(path).read_text(encoding="utf-8"), dialect=dialect)


def analyze_dbt_model(node: dict[str, Any], *, dialect: Optional[str] = None) -> ColumnLineage:
    """Analyze a dbt manifest model node's compiled/raw SQL."""
    sql = node.get("compiled_code") or node.get("raw_code") or node.get("raw_sql")
    if not sql:
        raise ValueError("model has no compiled_code/raw_code/raw_sql")
    return analyze_sql(str(sql), dialect=dialect)


__all__ = [
    "ColumnLineage",
    "LineageUnavailable",
    "analyze_dbt_model",
    "analyze_file",
    "analyze_sql",
]
