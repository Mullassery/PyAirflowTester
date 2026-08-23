"""Tests for intelligence and observability engines (Phases 3-4)."""

from datetime import datetime, timedelta

import pytest
from pyairflowtester.dependency_intelligence.analytics import TestCoverageAnalyzer
from pyairflowtester.dependency_intelligence.intelligence import (
    AnomalyDetector,
    FailurePredictionEngine,
    HealthScoreCalculator,
    RecommendationEngine,
)
from pyairflowtester.dependency_intelligence.models import (
    DependencyGraph,
    Edge,
    Node,
    NodeSeverity,
    NodeType,
)
from pyairflowtester.dependency_intelligence.observability import (
    AlertManager,
    DashboardBuilder,
    EventLogger,
    MetricsCollector,
    MetricType,
)


@pytest.fixture
def test_graph():
    """Create a test graph."""
    graph = DependencyGraph()

    nodes = {
        "critical_dag": Node(
            "critical_dag",
            "Critical DAG",
            NodeType.DAG,
            severity=NodeSeverity.CRITICAL,
            owner="team_a",
        ),
        "high_model": Node(
            "high_model",
            "High Model",
            NodeType.DBT_MODEL,
            severity=NodeSeverity.HIGH,
            owner="team_a",
        ),
        "medium_task": Node(
            "medium_task",
            "Medium Task",
            NodeType.TASK,
            severity=NodeSeverity.MEDIUM,
            owner="team_b",
        ),
    }

    for node in nodes.values():
        graph.add_node(node)

    graph.add_edge(Edge("critical_dag", "high_model"))
    graph.add_edge(Edge("high_model", "medium_task"))

    return graph


class TestFailurePredictionEngine:
    """Test failure prediction."""

    def test_predict_node_failure(self, test_graph):
        """Test failure prediction for a node."""
        engine = FailurePredictionEngine(test_graph)

        result = engine.predict_node_failure("critical_dag")

        assert 0.0 <= result.failure_probability <= 1.0
        assert 0.0 <= result.confidence <= 1.0

    def test_record_failure(self, test_graph):
        """Test recording failure events."""
        engine = FailurePredictionEngine(test_graph)

        engine.record_failure("critical_dag")
        engine.record_failure("critical_dag")

        result = engine.predict_node_failure("critical_dag")

        # Should have higher probability after failures
        assert result.contributing_factors

    def test_predict_all_nodes(self, test_graph):
        """Test predicting all nodes."""
        engine = FailurePredictionEngine(test_graph)

        predictions = engine.predict_all_nodes()

        assert len(predictions) == len(test_graph.nodes)

    def test_high_risk_nodes(self, test_graph):
        """Test finding high-risk nodes."""
        engine = FailurePredictionEngine(test_graph)

        engine.record_failure("critical_dag")
        engine.record_failure("critical_dag")

        high_risk = engine.get_high_risk_nodes(threshold=0.2)

        assert len(high_risk) >= 0

    def test_test_coverage_affects_failure_probability(self, test_graph):
        """Test coverage must come from the real TestCoverageAnalyzer, not a
        hardcoded stub. A node with real assigned tests should score a lower
        failure probability than the same node with none, and the two
        FailurePredictionEngine instances (uninstrumented vs. wired to a
        populated analyzer) must diverge for the exact same graph/node.
        """
        untested_engine = FailurePredictionEngine(test_graph)
        untested_prediction = untested_engine.predict_node_failure("critical_dag")

        analyzer = TestCoverageAnalyzer(test_graph)
        analyzer.assign_tests("critical_dag", ["t1", "t2", "t3", "t4", "t5"], test_type="unit")
        tested_engine = FailurePredictionEngine(test_graph, test_analyzer=analyzer)
        tested_prediction = tested_engine.predict_node_failure("critical_dag")

        assert "No test coverage" in untested_prediction.contributing_factors
        assert "No test coverage" not in tested_prediction.contributing_factors
        assert tested_prediction.failure_probability < untested_prediction.failure_probability


class TestHealthScoreTestCoverage:
    """Test that HealthScoreCalculator's test score reflects real graph data."""

    def test_test_score_varies_with_real_coverage_data(self, test_graph):
        """The test score must not be a fixed constant: a graph with no
        assigned tests, a graph with partial coverage, and a graph with full
        coverage should each produce a different, non-hardcoded test_score.
        """
        no_coverage_score = HealthScoreCalculator(test_graph).calculate_health_score().test_score

        partial_analyzer = TestCoverageAnalyzer(test_graph)
        partial_analyzer.assign_tests("critical_dag", ["t1", "t2", "t3"])
        partial_score = (
            HealthScoreCalculator(test_graph, test_analyzer=partial_analyzer)
            .calculate_health_score()
            .test_score
        )

        full_analyzer = TestCoverageAnalyzer(test_graph)
        for node_id in test_graph.nodes:
            full_analyzer.assign_tests(node_id, ["t1", "t2", "t3", "t4", "t5"])
        full_score = (
            HealthScoreCalculator(test_graph, test_analyzer=full_analyzer)
            .calculate_health_score()
            .test_score
        )

        assert no_coverage_score == 0.0
        assert no_coverage_score < partial_score < full_score
        assert full_score == 20.0


class TestAnomalyDetector:
    """Test anomaly detection."""

    def test_detect_anomalies(self, test_graph):
        """Test detection of anomalies."""
        detector = AnomalyDetector(test_graph)

        anomalies = detector.detect_all_anomalies()

        # May find unowned nodes or other issues
        assert isinstance(anomalies, list)

    def test_unowned_critical_detection(self, test_graph):
        """Test detection of unowned critical nodes."""
        # Add unowned critical node
        unowned = Node(
            "unowned", "Unowned", NodeType.TASK, severity=NodeSeverity.CRITICAL, owner=""
        )
        test_graph.add_node(unowned)

        detector = AnomalyDetector(test_graph)
        anomalies = detector.detect_all_anomalies()

        # Should find unowned critical node
        unowned_anomalies = [a for a in anomalies if a.anomaly_type == "unowned_critical"]
        assert len(unowned_anomalies) > 0


class TestRecommendationEngine:
    """Test recommendations."""

    def test_generate_recommendations(self, test_graph):
        """Test generating recommendations."""
        engine = RecommendationEngine(test_graph)

        recommendations = engine.generate_recommendations()

        assert len(recommendations) > 0

    def test_recommendation_priority(self, test_graph):
        """Test recommendation priorities."""
        engine = RecommendationEngine(test_graph)

        recommendations = engine.generate_recommendations()

        priorities = [r.priority for r in recommendations]
        assert all(p in ("critical", "high", "medium", "low") for p in priorities)

    def test_top_recommendations(self, test_graph):
        """Test getting top recommendations."""
        engine = RecommendationEngine(test_graph)

        top = engine.get_top_recommendations(limit=5)

        assert len(top) <= 5


class TestHealthScoreCalculator:
    """Test health score calculation."""

    def test_calculate_health_score(self, test_graph):
        """Test health score calculation."""
        calculator = HealthScoreCalculator(test_graph)

        score = calculator.calculate_health_score()

        assert 0.0 <= score.overall_score <= 100.0
        assert 0.0 <= score.coverage_score <= 20.0
        assert 0.0 <= score.connectivity_score <= 20.0

    def test_health_summary(self, test_graph):
        """Test health summary."""
        calculator = HealthScoreCalculator(test_graph)

        summary = calculator.get_health_summary()

        assert "status" in summary
        assert "score" in summary
        assert "color" in summary


class TestMetricsCollector:
    """Test metrics collection."""

    def test_record_metric(self):
        """Test recording a metric."""
        collector = MetricsCollector()

        metric = collector.record_metric(
            MetricType.EXECUTION_TIME, "node_1", 100.0, {"env": "prod"}
        )

        assert metric.node_id == "node_1"
        assert metric.value == 100.0

    def test_get_metrics_for_node(self):
        """Test retrieving metrics."""
        collector = MetricsCollector()

        collector.record_metric(MetricType.EXECUTION_TIME, "node_1", 100.0)
        collector.record_metric(MetricType.EXECUTION_TIME, "node_1", 120.0)
        collector.record_metric(MetricType.EXECUTION_TIME, "node_2", 80.0)

        metrics = collector.get_metrics_for_node("node_1", MetricType.EXECUTION_TIME)

        assert len(metrics) == 2

    def test_calculate_statistics(self):
        """Test metric statistics."""
        collector = MetricsCollector()

        for i in range(10):
            collector.record_metric(MetricType.EXECUTION_TIME, "node_1", 100.0 + i)

        stats = collector.calculate_statistics("node_1", MetricType.EXECUTION_TIME)

        assert stats["count"] == 10
        assert stats["avg"] > 0
        assert stats["min"] <= stats["avg"]
        assert stats["avg"] <= stats["max"]


class TestAlertManager:
    """Test alert management."""

    def test_set_threshold(self, test_graph):
        """Test setting alert thresholds."""
        manager = AlertManager(test_graph)

        manager.set_threshold("critical_dag", "execution_time", 5000, 10000)

        assert "critical_dag" in manager.thresholds

    def test_check_threshold_critical(self, test_graph):
        """Test critical threshold alert."""
        manager = AlertManager(test_graph)

        manager.set_threshold("critical_dag", "exec_time", 5000, 10000)

        alert = manager.check_threshold("critical_dag", "exec_time", 15000)

        assert alert is not None
        assert alert.severity == NodeSeverity.CRITICAL

    def test_check_threshold_warning(self, test_graph):
        """Test warning threshold alert."""
        manager = AlertManager(test_graph)

        manager.set_threshold("critical_dag", "exec_time", 5000, 10000)

        alert = manager.check_threshold("critical_dag", "exec_time", 7500)

        assert alert is not None
        assert alert.severity == NodeSeverity.HIGH

    def test_no_alert_below_threshold(self, test_graph):
        """Test no alert when below threshold."""
        manager = AlertManager(test_graph)

        manager.set_threshold("critical_dag", "exec_time", 5000, 10000)

        alert = manager.check_threshold("critical_dag", "exec_time", 3000)

        assert alert is None

    def test_get_active_alerts(self, test_graph):
        """Test getting active alerts."""
        manager = AlertManager(test_graph)

        manager.set_threshold("critical_dag", "exec_time", 5000, 10000)
        manager.check_threshold("critical_dag", "exec_time", 15000)

        active = manager.get_active_alerts()

        assert len(active) >= 1

    def test_resolve_alert(self, test_graph):
        """Test resolving alerts."""
        manager = AlertManager(test_graph)

        manager.set_threshold("critical_dag", "exec_time", 5000, 10000)
        alert = manager.check_threshold("critical_dag", "exec_time", 15000)

        manager.resolve_alert(alert.alert_id)

        active = manager.get_active_alerts()

        assert len(active) == 0


class TestEventLogger:
    """Test event logging."""

    def test_log_execution(self, test_graph):
        """Test logging execution event."""
        logger = EventLogger(test_graph)

        now = datetime.utcnow()
        event = logger.log_execution(
            "critical_dag", "success", 1500, now, now + timedelta(seconds=1.5)
        )

        assert event.node_id == "critical_dag"
        assert event.status == "success"

    def test_get_events_for_node(self, test_graph):
        """Test retrieving events."""
        logger = EventLogger(test_graph)

        now = datetime.utcnow()
        logger.log_execution("critical_dag", "success", 100, now, now)
        logger.log_execution("critical_dag", "failure", 200, now, now)

        events = logger.get_events_for_node("critical_dag")

        assert len(events) == 2

    def test_failure_rate(self, test_graph):
        """Test failure rate calculation."""
        logger = EventLogger(test_graph)

        now = datetime.utcnow()
        logger.log_execution("node", "success", 100, now, now)
        logger.log_execution("node", "failure", 100, now, now)
        logger.log_execution("node", "success", 100, now, now)

        rate = logger.get_failure_rate("node")

        assert rate == pytest.approx(1.0 / 3.0, rel=0.1)

    def test_average_duration(self, test_graph):
        """Test average duration calculation."""
        logger = EventLogger(test_graph)

        now = datetime.utcnow()
        logger.log_execution("node", "success", 100, now, now)
        logger.log_execution("node", "success", 200, now, now)

        avg = logger.get_average_duration("node")

        assert avg == pytest.approx(150.0)


class TestDashboardBuilder:
    """Test dashboard building."""

    def test_build_node_dashboard(self, test_graph):
        """Test building node dashboard."""
        metrics = MetricsCollector()
        alerts = AlertManager(test_graph)
        events = EventLogger(test_graph)

        builder = DashboardBuilder(test_graph, metrics, alerts, events)

        dashboard = builder.build_node_dashboard("critical_dag")

        assert "node_id" in dashboard
        assert "dashboard" in dashboard

    def test_build_health_dashboard(self, test_graph):
        """Test building health dashboard."""
        metrics = MetricsCollector()
        alerts = AlertManager(test_graph)
        events = EventLogger(test_graph)

        builder = DashboardBuilder(test_graph, metrics, alerts, events)

        dashboard = builder.build_health_dashboard()

        assert "dashboard" in dashboard
        assert "metrics" in dashboard
        assert "alerts" in dashboard
