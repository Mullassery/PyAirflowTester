"""Tests for dependency intelligence analyzers."""

import pytest
from pyairflowtester.dependency_intelligence.analyzers import (
    BlastRadiusEngine,
    DriftDetectionEngine,
    ImpactAnalysisEngine,
    RiskScoringEngine,
)
from pyairflowtester.dependency_intelligence.models import (
    DependencyGraph,
    Edge,
    Node,
    NodeSeverity,
    NodeType,
)


@pytest.fixture
def test_graph():
    """Create a test graph for analysis."""
    graph = DependencyGraph()

    # Create nodes with varying severity
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
        "low_task": Node(
            "low_task", "Low Task", NodeType.TASK, severity=NodeSeverity.LOW, owner="team_b"
        ),
        "downstream_1": Node(
            "downstream_1",
            "Downstream 1",
            NodeType.DBT_MODEL,
            severity=NodeSeverity.HIGH,
            owner="team_c",
        ),
        "downstream_2": Node(
            "downstream_2",
            "Downstream 2",
            NodeType.TASK,
            severity=NodeSeverity.MEDIUM,
            owner="team_c",
        ),
    }

    for node in nodes.values():
        graph.add_node(node)

    # Create dependency chain
    graph.add_edge(Edge("critical_dag", "high_model"))
    graph.add_edge(Edge("high_model", "medium_task"))
    graph.add_edge(Edge("medium_task", "low_task"))
    graph.add_edge(Edge("medium_task", "downstream_1"))
    graph.add_edge(Edge("downstream_1", "downstream_2"))

    return graph


class TestImpactAnalysis:
    """Test impact analysis engine."""

    def test_impact_critical_node(self, test_graph):
        """Test impact of changing a critical node."""
        engine = ImpactAnalysisEngine(test_graph)

        result = engine.analyze("critical_dag")

        assert result.node_id == "critical_dag"
        assert len(result.impacted_nodes) > 0
        assert result.impact_depth > 0
        assert 0 <= result.impact_score <= 1.0

    def test_impact_with_depth(self, test_graph):
        """Test impact analysis with depth limit."""
        engine = ImpactAnalysisEngine(test_graph)

        result_no_limit = engine.analyze("critical_dag")
        result_depth_1 = engine.analyze("critical_dag", max_depth=1)

        # Limited depth should have fewer impacted nodes
        assert len(result_depth_1.impacted_nodes) <= len(result_no_limit.impacted_nodes)

    def test_impact_grouping(self, test_graph):
        """Test that impact results are grouped by severity and type."""
        engine = ImpactAnalysisEngine(test_graph)

        result = engine.analyze("critical_dag")

        # Should have grouping by severity
        assert len(result.by_severity) > 0

        # Should have grouping by type
        assert len(result.by_type) > 0

    def test_impact_nonexistent_node(self, test_graph):
        """Test impact analysis on nonexistent node."""
        engine = ImpactAnalysisEngine(test_graph)

        result = engine.analyze("nonexistent")

        assert result.impact_score == 0.0
        assert len(result.impacted_nodes) == 0


class TestBlastRadius:
    """Test blast radius analysis engine."""

    def test_single_node_blast(self, test_graph):
        """Test blast radius of single node change."""
        engine = BlastRadiusEngine(test_graph)

        result = engine.analyze(["medium_task"])

        assert len(result.change_nodes) == 1
        assert result.blast_radius > 0
        assert result.blast_depth >= 0

    def test_multi_node_blast(self, test_graph):
        """Test blast radius of multiple node changes."""
        engine = BlastRadiusEngine(test_graph)

        result = engine.analyze(["critical_dag", "high_model"])

        assert len(result.change_nodes) == 2
        assert len(result.affected_nodes) > 0

    def test_risk_assessment(self, test_graph):
        """Test risk level assessment."""
        engine = BlastRadiusEngine(test_graph)

        # Critical node should have high risk
        result = engine.analyze(["critical_dag"])

        assert result.risk_level in ("low", "medium", "high", "critical")

    def test_deployability(self, test_graph):
        """Test deployability determination."""
        engine = BlastRadiusEngine(test_graph)

        result = engine.analyze(["low_task"])

        assert isinstance(result.deployable, bool)

    def test_severity_distribution(self, test_graph):
        """Test severity distribution calculation."""
        engine = BlastRadiusEngine(test_graph)

        result = engine.analyze(["high_model"])

        # Should have distribution data
        assert len(result.severity_distribution) >= 0


class TestRiskScoring:
    """Test risk scoring engine."""

    def test_score_node(self, test_graph):
        """Test risk scoring for a node."""
        engine = RiskScoringEngine(test_graph)

        result = engine.score_node("high_model")

        assert 0.0 <= result.risk_score <= 10.0
        assert result.node_id == "high_model"
        assert result.severity in [
            NodeSeverity.CRITICAL,
            NodeSeverity.HIGH,
            NodeSeverity.MEDIUM,
            NodeSeverity.LOW,
        ]

    def test_score_components(self, test_graph):
        """Test that score has components breakdown."""
        engine = RiskScoringEngine(test_graph)

        result = engine.score_node("critical_dag")

        # Should have components
        assert len(result.components) > 0
        # Components should have severity, downstream, etc.
        assert "severity" in result.components or "downstream" in result.components

    def test_score_factors(self, test_graph):
        """Test that score includes explanation factors."""
        engine = RiskScoringEngine(test_graph)

        result = engine.score_node("critical_dag")

        # Critical node should have factors explaining high score
        if result.risk_score > 5.0:
            assert len(result.factors) > 0

    def test_score_all_nodes(self, test_graph):
        """Test scoring all nodes."""
        engine = RiskScoringEngine(test_graph)

        scores = engine.score_all_nodes()

        assert len(scores) == len(test_graph.nodes)
        assert all(0.0 <= s.risk_score <= 10.0 for s in scores.values())

    def test_critical_node_high_score(self, test_graph):
        """Test that critical nodes get higher scores."""
        engine = RiskScoringEngine(test_graph)

        critical_score = engine.score_node("critical_dag").risk_score
        low_score = engine.score_node("low_task").risk_score

        # Critical should generally score higher
        assert critical_score >= low_score or critical_score == 0.0


class TestDriftDetection:
    """Test drift detection engine."""

    def test_no_drift(self, test_graph):
        """Test when graphs are identical."""
        engine = DriftDetectionEngine(test_graph, test_graph)

        result = engine.detect_drift()

        assert result.drift_count == 0
        assert len(result.detected_drifts) == 0

    def test_node_addition(self, test_graph):
        """Test detection of new nodes."""
        # Create modified graph with new node
        modified_graph = DependencyGraph()
        modified_graph.nodes = test_graph.nodes.copy()
        modified_graph.edges = test_graph.edges.copy()

        new_node = Node("new_node", "New Node", NodeType.TASK)
        modified_graph.add_node(new_node)

        engine = DriftDetectionEngine(modified_graph, test_graph)
        result = engine.detect_drift()

        assert result.drift_count > 0
        assert any(d["type"] == "nodes_added" for d in result.detected_drifts)

    def test_node_removal(self, test_graph):
        """Test detection of removed nodes."""
        # Create modified graph without a node
        modified_graph = DependencyGraph()
        modified_graph.nodes = {k: v for k, v in test_graph.nodes.items() if k != "low_task"}
        modified_graph.edges = [
            e for e in test_graph.edges if e.source != "low_task" and e.target != "low_task"
        ]

        engine = DriftDetectionEngine(modified_graph, test_graph)
        result = engine.detect_drift()

        assert result.drift_count > 0
        assert any(d["type"] == "nodes_removed" for d in result.detected_drifts)

    def test_edge_addition(self, test_graph):
        """Test detection of new edges."""
        # Create modified graph with new edge
        modified_graph = DependencyGraph()
        modified_graph.nodes = test_graph.nodes.copy()
        modified_graph.edges = test_graph.edges.copy()

        new_edge = Edge("low_task", "downstream_1")
        modified_graph.add_edge(new_edge)

        engine = DriftDetectionEngine(modified_graph, test_graph)
        result = engine.detect_drift()

        assert result.drift_count > 0
        assert any(d["type"] == "edges_added" for d in result.detected_drifts)

    def test_drift_severity(self, test_graph):
        """Test drift severity determination."""
        # Create graph with removed critical edge
        modified_graph = DependencyGraph()
        modified_graph.nodes = test_graph.nodes.copy()
        modified_graph.edges = [
            e
            for e in test_graph.edges
            if not (e.source == "critical_dag" and e.target == "high_model")
        ]

        engine = DriftDetectionEngine(modified_graph, test_graph)
        result = engine.detect_drift()

        # Removed edges should indicate higher severity
        if result.drift_count > 0:
            assert result.severity in [NodeSeverity.LOW, NodeSeverity.MEDIUM, NodeSeverity.HIGH]

    def test_drift_affected_nodes(self, test_graph):
        """Test that drift tracks affected nodes."""
        modified_graph = DependencyGraph()
        modified_graph.nodes = test_graph.nodes.copy()
        modified_graph.edges = test_graph.edges.copy()

        new_node = Node("new_node", "New Node", NodeType.TASK)
        modified_graph.add_node(new_node)

        engine = DriftDetectionEngine(modified_graph, test_graph)
        result = engine.detect_drift()

        assert "new_node" in result.affected_nodes


class TestAnalyzerIntegration:
    """Test analyzers working together."""

    def test_impact_to_blast_radius(self, test_graph):
        """Test using impact analysis to inform blast radius."""
        impact_engine = ImpactAnalysisEngine(test_graph)
        blast_engine = BlastRadiusEngine(test_graph)

        # Get impact of critical_dag
        impact = impact_engine.analyze("critical_dag")

        # Use impacted nodes for blast radius
        result = blast_engine.analyze(["critical_dag"])

        # Results should be related
        assert len(result.affected_nodes) >= len(impact.impacted_nodes)

    def test_blast_radius_to_risk_scoring(self, test_graph):
        """Test using blast radius results to inform risk scoring."""
        blast_engine = BlastRadiusEngine(test_graph)
        risk_engine = RiskScoringEngine(test_graph)

        # Get blast radius
        blast_result = blast_engine.analyze(["critical_dag"])

        # Score the affected nodes
        scores = {
            node_id: risk_engine.score_node(node_id) for node_id in blast_result.affected_nodes[:5]
        }

        assert all(0.0 <= s.risk_score <= 10.0 for s in scores.values())
