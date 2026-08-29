"""FastAPI web dashboard that serves DashboardBuilder output as real HTML.

This is the browsable counterpart to `pyairflowtester dependency ...`: it builds
the same unified dependency graph (from Airflow DAG files and/or a dbt
`manifest.json`) and renders `DashboardBuilder.build_node_dashboard()` /
`build_health_dashboard()` output as readable HTML pages instead of raw dicts.

Requires the optional `web` extra:

    pip install pyairflowtester[web]

Nothing else in the package imports this module, so a plain `pip install
pyairflowtester` (no extras) is unaffected by the fastapi/uvicorn/jinja2
dependency.
"""

from __future__ import annotations

import html as _html
from pathlib import Path
from typing import Any, List, Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
    from jinja2 import DictLoader, Environment, select_autoescape
    from markupsafe import Markup
except ImportError as exc:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        "The PyAirflowTester web dashboard requires optional dependencies "
        "(fastapi, uvicorn, jinja2). Install them with:\n\n"
        "    pip install pyairflowtester[web]\n"
    ) from exc

from pyairflowtester.dependency_intelligence.models import DependencyGraph
from pyairflowtester.dependency_intelligence.observability import (
    AlertManager,
    DashboardBuilder,
    EventLogger,
    MetricsCollector,
)
from pyairflowtester.dependency_intelligence.parsers import UnifiedGraphBuilder

# --------------------------------------------------------------------------
# Rendering helpers: turn arbitrary dict/list output from DashboardBuilder
# into real HTML tables/lists, not a JSON dump styled with CSS.
# --------------------------------------------------------------------------


def _render_value(value: Any) -> str:
    """Recursively render a Python value (from a DashboardBuilder dict) as HTML."""
    if isinstance(value, dict):
        if not value:
            return '<p class="muted">(empty)</p>'
        rows = "".join(
            f"<tr><th>{_html.escape(str(k))}</th><td>{_render_value(v)}</td></tr>"
            for k, v in value.items()
        )
        return f'<table class="kv">{rows}</table>'

    if isinstance(value, (list, tuple)):
        if not value:
            return '<p class="muted">(none)</p>'
        if all(isinstance(item, dict) for item in value):
            # Union of keys across all rows, in first-seen order.
            columns: List[str] = []
            for item in value:
                for k in item:
                    if k not in columns:
                        columns.append(k)
            header = "".join(f"<th>{_html.escape(c)}</th>" for c in columns)
            body = "".join(
                "<tr>"
                + "".join(f"<td>{_render_value(item.get(c, ''))}</td>" for c in columns)
                + "</tr>"
                for item in value
            )
            return (
                f'<table class="list-table"><thead><tr>{header}</tr></thead>'
                f"<tbody>{body}</tbody></table>"
            )
        items = "".join(f"<li>{_render_value(item)}</li>" for item in value)
        return f"<ul>{items}</ul>"

    if value is None or value == "":
        return '<span class="muted">&mdash;</span>'

    return _html.escape(str(value))


# --------------------------------------------------------------------------
# Templates (kept inline as plain strings so the package needs no extra
# packaged data files / MANIFEST entries).
# --------------------------------------------------------------------------

_BASE_CSS = """
:root { color-scheme: light dark; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  margin: 0; padding: 0;
  background: #f6f7f9; color: #1a1a1a;
}
header {
  background: #1d2333; color: #fff; padding: 1rem 1.5rem;
  display: flex; align-items: baseline; gap: 1rem;
}
header a { color: #cfe0ff; text-decoration: none; font-weight: 600; }
header a:hover { text-decoration: underline; }
header .tagline { color: #9aa4c0; font-size: 0.85rem; }
main { max-width: 1000px; margin: 1.5rem auto; padding: 0 1.5rem 3rem; }
h1 { font-size: 1.4rem; margin-top: 0; }
h2 { font-size: 1.05rem; margin-top: 2rem; border-bottom: 1px solid #ddd; padding-bottom: 0.3rem; }
table { border-collapse: collapse; width: 100%; margin: 0.5rem 0 1rem; background: #fff; }
table.kv th, table.kv td, table.list-table th, table.list-table td,
table.index th, table.index td {
  border: 1px solid #e0e2e7; padding: 0.4rem 0.6rem; text-align: left; vertical-align: top;
  font-size: 0.92rem;
}
table.kv th { width: 220px; background: #f0f2f6; font-weight: 600; }
table.list-table thead th, table.index thead th { background: #f0f2f6; font-weight: 600; }
a.node-link { color: #2454c7; text-decoration: none; font-weight: 600; }
a.node-link:hover { text-decoration: underline; }
.muted { color: #888; }
.badge {
  display: inline-block; padding: 0.1rem 0.5rem; border-radius: 3px;
  font-size: 0.78rem; font-weight: 600; color: #fff;
}
.badge.critical { background: #c0392b; }
.badge.high { background: #d35400; }
.badge.medium { background: #b8860b; }
.badge.low { background: #2e7d32; }
.stats { display: flex; gap: 1.5rem; margin: 1rem 0; flex-wrap: wrap; }
.stat { background: #fff; border: 1px solid #e0e2e7; border-radius: 6px; padding: 0.75rem 1.25rem; }
.stat .n { font-size: 1.6rem; font-weight: 700; display: block; }
.stat .l { font-size: 0.78rem; color: #666; text-transform: uppercase; letter-spacing: 0.03em; }
@media (prefers-color-scheme: dark) {
  body { background: #16181d; color: #e6e6e6; }
  header { background: #10131c; }
  table, .stat { background: #1e2129; }
  table.kv th, table.kv td, table.list-table th, table.list-table td,
  table.index th, table.index td { border-color: #2c303a; }
  table.kv th, table.list-table thead th, table.index thead th { background: #262a34; }
  h2 { border-bottom-color: #2c303a; }
  a.node-link { color: #7aa2f7; }
}
"""

_TEMPLATES = {
    "base.html": """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}PyAirflowTester Dashboard{% endblock %}</title>
<style>""" + _BASE_CSS + """</style>
</head>
<body>
<header>
  <a href="/">PyAirflowTester</a>
  <span class="tagline">dependency intelligence dashboard</span>
  <span style="flex:1"></span>
  <a href="/">Nodes</a>
  <a href="/health">System Health</a>
</header>
<main>
{% block content %}{% endblock %}
</main>
</body>
</html>
""",
    "index.html": """{% extends "base.html" %}
{% block title %}Nodes &mdash; PyAirflowTester Dashboard{% endblock %}
{% block content %}
<h1>Dependency Graph</h1>
<div class="stats">
  <div class="stat"><span class="n">{{ node_count }}</span><span class="l">Nodes</span></div>
  <div class="stat"><span class="n">{{ edge_count }}</span><span class="l">Edges</span></div>
</div>
{% if nodes %}
<table class="index">
<thead><tr><th>Name</th><th>Type</th><th>Severity</th><th>Owner</th><th>Upstream</th><th>Downstream</th></tr></thead>
<tbody>
{% for node in nodes %}
<tr>
  <td><a class="node-link" href="/nodes/{{ node.id }}">{{ node.name }}</a></td>
  <td>{{ node.type.value }}</td>
  <td><span class="badge {{ node.severity.value }}">{{ node.severity.value }}</span></td>
  <td>{{ node.owner or "&mdash;" | safe }}</td>
  <td>{{ node.upstream_count }}</td>
  <td>{{ node.downstream_count }}</td>
</tr>
{% endfor %}
</tbody>
</table>
{% else %}
<p class="muted">No nodes in the graph. Pass --dags and/or --dbt-manifest when running
<code>pyairflowtester serve</code> to build one.</p>
{% endif %}
{% endblock %}
""",
    "node.html": """{% extends "base.html" %}
{% block title %}{{ node_id }} &mdash; PyAirflowTester Dashboard{% endblock %}
{% block content %}
<p><a href="/">&larr; All nodes</a></p>
<h1>{{ dashboard.node_name }}</h1>
<p class="muted">{{ node_id }}</p>
{{ content }}
{% endblock %}
""",
    "health.html": """{% extends "base.html" %}
{% block title %}System Health &mdash; PyAirflowTester Dashboard{% endblock %}
{% block content %}
<p><a href="/">&larr; All nodes</a></p>
<h1>System Health</h1>
{{ content }}
{% endblock %}
""",
}

_env = Environment(
    loader=DictLoader(_TEMPLATES),
    autoescape=select_autoescape(["html"]),
)


# --------------------------------------------------------------------------
# App factory
# --------------------------------------------------------------------------


def create_app(
    graph: DependencyGraph,
    metrics_collector: Optional[MetricsCollector] = None,
    alert_manager: Optional[AlertManager] = None,
    event_logger: Optional[EventLogger] = None,
) -> "FastAPI":
    """Build a FastAPI app that serves DashboardBuilder output for `graph`.

    Reuses the existing `DashboardBuilder` (python/pyairflowtester/
    dependency_intelligence/observability.py) rather than reimplementing any
    dashboard logic here -- this module is purely a rendering layer.
    """
    metrics_collector = metrics_collector or MetricsCollector()
    alert_manager = alert_manager or AlertManager(graph)
    event_logger = event_logger or EventLogger(graph)
    builder = DashboardBuilder(graph, metrics_collector, alert_manager, event_logger)

    app = FastAPI(
        title="PyAirflowTester Dashboard",
        description="Browsable dependency-intelligence dashboard for PyAirflowTester.",
    )
    app.state.graph = graph
    app.state.builder = builder

    @app.get("/", response_class=HTMLResponse)
    def list_nodes() -> str:
        """List all DAGs/tasks/models/etc. currently in the dependency graph."""
        nodes = sorted(graph.nodes.values(), key=lambda n: (n.type.value, n.name))
        template = _env.get_template("index.html")
        return template.render(
            nodes=nodes, node_count=len(graph.nodes), edge_count=len(graph.edges)
        )

    @app.get("/nodes/{node_id}", response_class=HTMLResponse)
    def node_dashboard(node_id: str) -> str:
        """Render DashboardBuilder.build_node_dashboard(node_id) as HTML."""
        if node_id not in graph.nodes:
            raise HTTPException(status_code=404, detail=f"Unknown node: {node_id!r}")
        dashboard = builder.build_node_dashboard(node_id)
        content = Markup(_render_value(dashboard))
        template = _env.get_template("node.html")
        return template.render(node_id=node_id, dashboard=dashboard, content=content)

    @app.get("/health", response_class=HTMLResponse)
    def health_dashboard() -> str:
        """Render DashboardBuilder.build_health_dashboard() as HTML."""
        dashboard = builder.build_health_dashboard()
        content = Markup(_render_value(dashboard))
        template = _env.get_template("health.html")
        return template.render(content=content)

    return app


def build_app_from_sources(
    dags: Optional[str] = None,
    dbt_manifest: Optional[str] = None,
) -> "FastAPI":
    """Build the dependency graph from DAG files / a dbt manifest, then serve it.

    Mirrors the source-collection logic used by `pyairflowtester dependency
    build/impact/lineage/...` (see dependency_intelligence/cli.py) so `serve`
    accepts the same --dags/--dbt-manifest options as the rest of the CLI.
    """
    dag_files: List[str] = []
    if dags:
        dag_files = [str(p) for p in Path(dags).glob("**/*.py")]

    graph = UnifiedGraphBuilder.build_unified_graph(
        dag_files=dag_files,
        dbt_manifest=dbt_manifest,
    )
    return create_app(graph)
