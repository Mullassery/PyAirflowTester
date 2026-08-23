"""Analytics engines for dependency intelligence (Phase 2: Weeks 5-8)."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from .graph import DependencyGraphEngine
from .models import (
    DependencyGraph,
    NodeSeverity,
    NodeType,
)

logger = logging.getLogger(__name__)


@dataclass
class OwnershipAnalysis:
    """Ownership and team impact analysis."""

    owner: str
    owned_nodes: List[str]
    downstream_impact: int
    critical_dependencies: List[str]
    team_risk_score: float
    affected_teams: Set[str]
    cross_team_edges: int


@dataclass
class SchemaEvolution:
    """Schema change tracking."""

    node_id: str
    changed_at: datetime
    change_type: str  # added_column, removed_column, type_change, renamed
    old_schema: Dict
    new_schema: Dict
    affected_downstream: List[str]


@dataclass
class SLAValidation:
    """SLA compliance tracking."""

    node_id: str
    has_sla: bool
    sla_target: Optional[str]
    actual_performance: Optional[str]
    compliance_status: str  # compliant, at_risk, violated
    severity: NodeSeverity


@dataclass
class TestCoverageAnalysis:
    """Test coverage metrics."""

    node_id: str
    total_tests: int
    test_types: Dict[str, int]  # unit, integration, end_to_end
    coverage_percentage: float
    coverage_status: str  # good, adequate, poor
    missing_tests: List[str]


class OwnershipAnalyzer:
    """Analyze ownership and team impact."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.engine = DependencyGraphEngine(graph)

    def analyze_owner(self, owner: str) -> OwnershipAnalysis:
        """
        Analyze impact and dependencies for an owner/team.

        Returns ownership analysis with risk metrics.
        """
        # Get all nodes owned by this owner
        owned_nodes = [n.id for n in self.graph.nodes.values() if n.owner == owner]

        # Calculate downstream impact
        all_downstream = set()
        for node_id in owned_nodes:
            all_downstream.update(self.engine.get_downstream_nodes(node_id))

        # Get critical upstream dependencies
        critical_deps = []
        for node_id in owned_nodes:
            upstream = self.engine.get_upstream_nodes(node_id)
            for up_id in upstream:
                node = self.graph.nodes.get(up_id)
                if node and node.severity == NodeSeverity.CRITICAL:
                    critical_deps.append(up_id)

        # Get all affected teams
        affected_teams = set()
        for node_id in all_downstream:
            node = self.graph.nodes.get(node_id)
            if node and node.owner != owner:
                affected_teams.add(node.owner)

        # Count cross-team edges
        cross_team_edges = 0
        for edge in self.graph.edges:
            source = self.graph.nodes.get(edge.source)
            target = self.graph.nodes.get(edge.target)
            if source and target and source.owner != target.owner:
                if source.owner == owner or target.owner == owner:
                    cross_team_edges += 1

        # Calculate team risk score
        team_risk = self._calculate_team_risk(
            len(owned_nodes), len(all_downstream), len(critical_deps), len(affected_teams)
        )

        return OwnershipAnalysis(
            owner=owner,
            owned_nodes=owned_nodes,
            downstream_impact=len(all_downstream),
            critical_dependencies=list(set(critical_deps)),
            team_risk_score=team_risk,
            affected_teams=affected_teams,
            cross_team_edges=cross_team_edges,
        )

    def _calculate_team_risk(self, owned: int, downstream: int, critical: int, teams: int) -> float:
        """Calculate team risk score (0-10)."""
        score = 0.0

        # Owned node count factor
        if owned > 100:
            score += 2.0
        elif owned > 50:
            score += 1.0

        # Downstream impact factor
        if downstream > 200:
            score += 3.0
        elif downstream > 100:
            score += 2.0
        elif downstream > 50:
            score += 1.0

        # Critical dependency factor
        if critical > 5:
            score += 2.0
        elif critical > 0:
            score += 1.0

        # Team coordination complexity
        score += min(3.0, teams / 5.0)

        return min(10.0, score)

    def analyze_all_owners(self) -> Dict[str, OwnershipAnalysis]:
        """Analyze all owners/teams."""
        owners = set(n.owner for n in self.graph.nodes.values() if n.owner)
        return {owner: self.analyze_owner(owner) for owner in owners}

    def find_critical_ownership_gaps(self) -> List[Tuple[str, str]]:
        """Find nodes with no owner."""
        unowned = [(n.id, n.name) for n in self.graph.nodes.values() if not n.owner]
        return unowned


class SchemaEvolutionTracker:
    """Track schema changes and impact."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.engine = DependencyGraphEngine(graph)
        self.evolution_history: List[SchemaEvolution] = []

    def add_schema_change(
        self, node_id: str, change_type: str, old_schema: Dict, new_schema: Dict
    ) -> SchemaEvolution:
        """Record a schema change."""
        downstream = self.engine.get_downstream_nodes(node_id)

        evolution = SchemaEvolution(
            node_id=node_id,
            changed_at=datetime.utcnow(),
            change_type=change_type,
            old_schema=old_schema,
            new_schema=new_schema,
            affected_downstream=downstream,
        )

        self.evolution_history.append(evolution)
        return evolution

    def detect_breaking_changes(self) -> List[SchemaEvolution]:
        """Identify potentially breaking schema changes."""
        breaking = []

        for evolution in self.evolution_history:
            # Check for removed fields
            old_fields = set(evolution.old_schema.get("fields", []))
            new_fields = set(evolution.new_schema.get("fields", []))
            removed = old_fields - new_fields

            if removed and evolution.affected_downstream:
                breaking.append(evolution)

            # Check for type changes
            for field in old_fields & new_fields:
                old_type = evolution.old_schema.get("fields", {}).get(field, {}).get("type")
                new_type = evolution.new_schema.get("fields", {}).get(field, {}).get("type")

                if old_type and new_type and old_type != new_type:
                    if evolution.affected_downstream:
                        breaking.append(evolution)

        return breaking

    def get_evolution_timeline(self, node_id: str) -> List[SchemaEvolution]:
        """Get schema evolution timeline for a node."""
        return [e for e in self.evolution_history if e.node_id == node_id]


class SLAValidator:
    """Validate SLA compliance."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.sla_definitions: Dict[str, str] = {}
        self.performance_metrics: Dict[str, str] = {}

    def set_sla(self, node_id: str, sla_target: str) -> None:
        """Set SLA target for a node."""
        self.sla_definitions[node_id] = sla_target

    def record_performance(self, node_id: str, actual: str) -> None:
        """Record actual performance."""
        self.performance_metrics[node_id] = actual

    def validate_node(self, node_id: str) -> SLAValidation:
        """Validate SLA compliance for a node."""
        has_sla = node_id in self.sla_definitions
        sla_target = self.sla_definitions.get(node_id)
        actual = self.performance_metrics.get(node_id)

        node = self.graph.nodes.get(node_id)
        severity = node.severity if node else NodeSeverity.MEDIUM

        # Determine compliance status
        if not has_sla:
            compliance_status = "no_sla"
        elif not actual:
            compliance_status = "pending"
        elif self._is_compliant(sla_target, actual):
            compliance_status = "compliant"
        else:
            compliance_status = "violated"

        return SLAValidation(
            node_id=node_id,
            has_sla=has_sla,
            sla_target=sla_target,
            actual_performance=actual,
            compliance_status=compliance_status,
            severity=severity,
        )

    def _is_compliant(self, target: str, actual: str) -> bool:
        """Check if actual meets target."""
        # Simple comparison (can be enhanced)
        try:
            target_val = float(target.replace("ms", "").replace("s", ""))
            actual_val = float(actual.replace("ms", "").replace("s", ""))
            return actual_val <= target_val
        except (ValueError, AttributeError):
            return False

    def validate_all(self) -> Dict[str, SLAValidation]:
        """Validate all nodes with SLAs."""
        return {node_id: self.validate_node(node_id) for node_id in self.sla_definitions}

    def get_sla_violations(self) -> List[SLAValidation]:
        """Get nodes violating SLAs."""
        validations = self.validate_all()
        return [v for v in validations.values() if v.compliance_status == "violated"]

    def get_missing_slas(self) -> List[str]:
        """Get critical nodes without SLAs."""
        critical_nodes = [
            n.id for n in self.graph.nodes.values() if n.severity == NodeSeverity.CRITICAL
        ]
        return [n for n in critical_nodes if n not in self.sla_definitions]


class TestCoverageAnalyzer:
    """Analyze test coverage for nodes."""

    # Not a pytest test case; this only starts with "Test" because it
    # analyzes test coverage. Prevents pytest from warning when it tries
    # (and fails) to collect this as a test class.
    __test__ = False

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.test_assignments: Dict[str, List[str]] = {}

    def assign_tests(self, node_id: str, tests: List[str], test_type: str = "unit") -> None:
        """Assign tests to a node."""
        if node_id not in self.test_assignments:
            self.test_assignments[node_id] = []

        # Add tests with type metadata
        for test in tests:
            self.test_assignments[node_id].append(f"{test}:{test_type}")

    def analyze_coverage(self, node_id: str) -> TestCoverageAnalysis:
        """Analyze test coverage for a node."""
        tests = self.test_assignments.get(node_id, [])

        # Count test types
        test_types = {}
        for test in tests:
            parts = test.split(":")
            ttype = parts[1] if len(parts) > 1 else "unit"
            test_types[ttype] = test_types.get(ttype, 0) + 1

        # Calculate coverage percentage
        coverage = min(100.0, (len(tests) / 5.0) * 100) if tests else 0.0

        # Determine status
        if coverage >= 80:
            status = "good"
        elif coverage >= 50:
            status = "adequate"
        else:
            status = "poor"

        # Identify missing tests
        node = self.graph.nodes.get(node_id)
        missing = []
        if node:
            if node.type == NodeType.DBT_MODEL and not tests:
                missing.append("dbt_test")
            if node.severity == NodeSeverity.CRITICAL and len(tests) < 3:
                missing.append("additional_tests")

        return TestCoverageAnalysis(
            node_id=node_id,
            total_tests=len(tests),
            test_types=test_types,
            coverage_percentage=coverage,
            coverage_status=status,
            missing_tests=missing,
        )

    def analyze_all(self) -> Dict[str, TestCoverageAnalysis]:
        """Analyze coverage for all nodes with tests."""
        return {node_id: self.analyze_coverage(node_id) for node_id in self.test_assignments}

    def get_poorly_tested_nodes(self) -> List[str]:
        """Get nodes with poor test coverage."""
        analyses = self.analyze_all()
        return [
            node_id for node_id, analysis in analyses.items() if analysis.coverage_status == "poor"
        ]

    def get_critical_test_gaps(self) -> List[Tuple[str, List[str]]]:
        """Get critical nodes missing tests."""
        gaps = []
        for node_id, analysis in self.analyze_all().items():
            node = self.graph.nodes.get(node_id)
            if node and node.severity == NodeSeverity.CRITICAL:
                if analysis.total_tests == 0:
                    gaps.append((node_id, ["all_types"]))
                elif analysis.missing_tests:
                    gaps.append((node_id, analysis.missing_tests))

        return gaps
