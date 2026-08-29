"""Tests for the optional FastAPI web dashboard (pyairflowtester[web]).

Uses FastAPI's TestClient (backed by httpx) so no real socket/port is bound.
"""

from datetime import datetime, timedelta

import pytest

fastapi_testclient = pytest.importorskip(
    "fastapi.testclient", reason="requires the 'web' extra (pip install pyairflowtester[web])"
)

from pyairflowtester.dependency_intelligence.models import (  # noqa: E402
    DependencyGraph,
    Edge,
    Node,
    NodeSeverity,
    NodeType,
    RelationshipType,
)
from pyairflowtester.dependency_intelligence.observability import (  # noqa: E402
    AlertManager,
    EventLogger,
    MetricsCollector,
)
from pyairflowtester.web.app import create_app  # noqa: E402

TestClient = fastapi_testclient.TestClient


@pytest.fixture
def graph():
    """A small, realistic dependency graph: one DAG feeding a dbt model."""
    g = DependencyGraph()
    g.add_node(
        Node(
            "dag_orders",
            "orders_dag",
            NodeType.DAG,
            owner="team_data",
            severity=NodeSeverity.CRITICAL,
        )
    )
    g.add_node(
        Node(
            "model_fact_orders",
            "fact_orders",
            NodeType.DBT_MODEL,
            owner="team_analytics",
            severity=NodeSeverity.HIGH,
        )
    )
    g.add_edge(
        Edge("dag_orders", "model_fact_orders", relationship_type=RelationshipType.TRIGGERS)
    )
    return g


@pytest.fixture
def client(graph):
    events = EventLogger(graph)
    now = datetime.utcnow()
    events.log_execution(
        node_id="dag_orders",
        status="success",
        duration_ms=1200,
        start_time=now - timedelta(hours=1),
        end_time=now - timedelta(hours=1) + timedelta(milliseconds=1200),
    )
    events.log_execution(
        node_id="dag_orders",
        status="failure",
        duration_ms=500,
        start_time=now - timedelta(minutes=30),
        end_time=now - timedelta(minutes=30) + timedelta(milliseconds=500),
        error_message="connection timeout",
    )

    metrics = MetricsCollector()
    alerts = AlertManager(graph)

    app = create_app(graph, metrics_collector=metrics, alert_manager=alerts, event_logger=events)
    return TestClient(app)


def test_index_lists_nodes(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "orders_dag" in body
    assert "fact_orders" in body
    # Links to the node dashboard route.
    assert "/nodes/dag_orders" in body
    assert "/nodes/model_fact_orders" in body


def test_index_shows_graph_stats(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert "2" in body  # node_count
    assert "Nodes" in body
    assert "Edges" in body


def test_node_dashboard_renders_known_node(client):
    response = client.get("/nodes/dag_orders")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "orders_dag" in body
    assert "dag_orders" in body
    # Reliability section from DashboardBuilder.build_node_dashboard.
    assert "failure_rate" in body
    assert "connection timeout" in body
    # It's a real HTML table, not a JSON dump.
    assert "<table" in body
    assert '{"node_id"' not in body


def test_node_dashboard_second_node(client):
    response = client.get("/nodes/model_fact_orders")
    assert response.status_code == 200
    assert "fact_orders" in response.text


def test_node_dashboard_unknown_node_is_404(client):
    response = client.get("/nodes/does_not_exist")
    assert response.status_code == 404


def test_health_dashboard_renders(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.text
    assert "System Health" in body
    assert "total_nodes" in body
    assert "<table" in body


def test_build_app_from_sources_with_no_sources_yields_empty_graph():
    from pyairflowtester.web.app import build_app_from_sources

    app = build_app_from_sources(dags=None, dbt_manifest=None)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert len(app.state.graph.nodes) == 0
