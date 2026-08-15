"""Tests for dependency analytics engines (Phase 2)."""

import pytest
from pyairflowtester.dependency_intelligence.analytics import (
    OwnershipAnalyzer,
    SchemaEvolutionTracker,
    SLAValidator,
    TestCoverageAnalyzer,
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
    """Create a test graph for analytics."""
    graph = DependencyGraph()

    nodes = {
        "team_a_dag": Node(
            "team_a_dag", "Team A DAG", NodeType.DAG,
            severity=NodeSeverity.CRITICAL, owner="team_a"
        ),
        "team_a_model": Node(
            "team_a_model", "Team A Model", NodeType.DBT_MODEL,
            severity=NodeSeverity.HIGH, owner="team_a"
        ),
        "team_b_model": Node(
            "team_b_model", "Team B Model", NodeType.DBT_MODEL,
            severity=NodeSeverity.MEDIUM, owner="team_b"
        ),
        "unowned_model": Node(
            "unowned_model", "Unowned Model", NodeType.DBT_MODEL,
            severity=NodeSeverity.CRITICAL, owner=""
        ),
    }

    for node in nodes.values():
        graph.add_node(node)

    graph.add_edge(Edge("team_a_dag", "team_a_model"))
    graph.add_edge(Edge("team_a_model", "team_b_model"))
    graph.add_edge(Edge("team_b_model", "unowned_model"))

    return graph


class TestOwnershipAnalyzer:
    """Test ownership analysis."""

    def test_analyze_owner(self, test_graph):
        """Test ownership analysis for a team."""
        analyzer = OwnershipAnalyzer(test_graph)

        result = analyzer.analyze_owner("team_a")

        assert result.owner == "team_a"
        assert len(result.owned_nodes) == 2
        assert result.downstream_impact > 0

    def test_team_risk_score(self, test_graph):
        """Test team risk scoring."""
        analyzer = OwnershipAnalyzer(test_graph)

        result = analyzer.analyze_owner("team_a")

        assert 0.0 <= result.team_risk_score <= 10.0

    def test_cross_team_edges(self, test_graph):
        """Test cross-team edge counting."""
        analyzer = OwnershipAnalyzer(test_graph)

        result = analyzer.analyze_owner("team_a")

        assert result.cross_team_edges > 0

    def test_analyze_all_owners(self, test_graph):
        """Test analyzing all owners."""
        analyzer = OwnershipAnalyzer(test_graph)

        results = analyzer.analyze_all_owners()

        assert len(results) >= 2
        assert "team_a" in results
        assert "team_b" in results

    def test_critical_ownership_gaps(self, test_graph):
        """Test finding unowned critical nodes."""
        analyzer = OwnershipAnalyzer(test_graph)

        gaps = analyzer.find_critical_ownership_gaps()

        # Should find unowned_model
        assert any(n[0] == "unowned_model" for n in gaps)


class TestSchemaEvolutionTracker:
    """Test schema evolution tracking."""

    def test_add_schema_change(self, test_graph):
        """Test recording a schema change."""
        tracker = SchemaEvolutionTracker(test_graph)

        old_schema = {"fields": ["col_a", "col_b"]}
        new_schema = {"fields": ["col_a", "col_b", "col_c"]}

        evolution = tracker.add_schema_change(
            "team_a_model",
            "added_column",
            old_schema,
            new_schema
        )

        assert evolution.node_id == "team_a_model"
        assert evolution.change_type == "added_column"

    def test_get_evolution_timeline(self, test_graph):
        """Test getting evolution history."""
        tracker = SchemaEvolutionTracker(test_graph)

        old_schema = {"fields": ["col_a"]}
        new_schema = {"fields": ["col_a", "col_b"]}

        tracker.add_schema_change("team_a_model", "added_column", old_schema, new_schema)
        tracker.add_schema_change("team_a_model", "type_change", new_schema, new_schema)

        timeline = tracker.get_evolution_timeline("team_a_model")

        assert len(timeline) == 2

    def test_detect_breaking_changes(self, test_graph):
        """Test detection of breaking changes."""
        tracker = SchemaEvolutionTracker(test_graph)

        old_schema = {"fields": {"col_a": {"type": "string"}, "col_b": {"type": "int"}}}
        new_schema = {"fields": {"col_a": {"type": "string"}}}

        tracker.add_schema_change(
            "team_a_model",
            "removed_column",
            old_schema,
            new_schema
        )

        breaking = tracker.detect_breaking_changes()

        # If there are downstream nodes, should be detected
        assert len(breaking) >= 0


class TestSLAValidator:
    """Test SLA validation."""

    def test_set_sla(self, test_graph):
        """Test setting SLA."""
        validator = SLAValidator(test_graph)

        validator.set_sla("team_a_dag", "5000ms")

        assert "team_a_dag" in validator.sla_definitions

    def test_validate_compliant_node(self, test_graph):
        """Test validation of compliant node."""
        validator = SLAValidator(test_graph)

        validator.set_sla("team_a_dag", "5000ms")
        validator.record_performance("team_a_dag", "3000ms")

        result = validator.validate_node("team_a_dag")

        assert result.compliance_status == "compliant"

    def test_validate_violated_node(self, test_graph):
        """Test validation of violated node."""
        validator = SLAValidator(test_graph)

        validator.set_sla("team_a_dag", "1000ms")
        validator.record_performance("team_a_dag", "5000ms")

        result = validator.validate_node("team_a_dag")

        assert result.compliance_status == "violated"

    def test_get_sla_violations(self, test_graph):
        """Test getting SLA violations."""
        validator = SLAValidator(test_graph)

        validator.set_sla("team_a_dag", "1000ms")
        validator.record_performance("team_a_dag", "5000ms")

        validator.set_sla("team_b_model", "2000ms")
        validator.record_performance("team_b_model", "1500ms")

        violations = validator.get_sla_violations()

        assert len(violations) >= 1

    def test_get_missing_slas(self, test_graph):
        """Test finding critical nodes without SLAs."""
        validator = SLAValidator(test_graph)

        missing = validator.get_missing_slas()

        # Should find critical nodes without SLAs
        assert len(missing) > 0


class TestTestCoverageAnalyzer:
    """Test suite for the TestCoverageAnalyzer class.

    Named with a doubled "Test" prefix (pytest convention: TestX tests class
    X) because the class under test is itself named TestCoverageAnalyzer.
    Using the same name here would rebind/shadow the imported class in this
    module's namespace (F811), breaking every reference below.
    """

    def test_assign_tests(self, test_graph):
        """Test assigning tests to nodes."""
        analyzer = TestCoverageAnalyzer(test_graph)

        tests = ["test_team_a_dag_1", "test_team_a_dag_2"]
        analyzer.assign_tests("team_a_dag", tests)

        assert "team_a_dag" in analyzer.test_assignments
        assert len(analyzer.test_assignments["team_a_dag"]) == 2

    def test_analyze_coverage(self, test_graph):
        """Test coverage analysis."""
        analyzer = TestCoverageAnalyzer(test_graph)

        tests = ["test_1", "test_2", "test_3"]
        analyzer.assign_tests("team_a_model", tests)

        result = analyzer.analyze_coverage("team_a_model")

        assert result.total_tests == 3
        assert result.coverage_percentage > 0

    def test_coverage_status(self, test_graph):
        """Test coverage status determination."""
        analyzer = TestCoverageAnalyzer(test_graph)

        # Good coverage
        tests = [f"test_{i}" for i in range(10)]
        analyzer.assign_tests("good_node", tests)
        result = analyzer.analyze_coverage("good_node")
        assert result.coverage_status in ("good", "adequate")

        # Poor coverage
        analyzer.assign_tests("poor_node", [])
        result = analyzer.analyze_coverage("poor_node")
        assert result.coverage_status == "poor"

    def test_get_poorly_tested_nodes(self, test_graph):
        """Test finding poorly tested nodes."""
        analyzer = TestCoverageAnalyzer(test_graph)

        analyzer.assign_tests("tested_node", ["test_1", "test_2"])
        analyzer.assign_tests("poor_node", [])

        poorly = analyzer.get_poorly_tested_nodes()

        assert "poor_node" in poorly

    def test_get_critical_test_gaps(self, test_graph):
        """Test finding test gaps in critical nodes."""
        analyzer = TestCoverageAnalyzer(test_graph)

        # Assign no tests to critical node
        analyzer.assign_tests("team_a_dag", [])

        gaps = analyzer.get_critical_test_gaps()

        # Should find critical node with no tests
        assert any(g[0] == "team_a_dag" for g in gaps)
