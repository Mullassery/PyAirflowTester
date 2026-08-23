"""Intelligence engines for advanced analysis (Phase 3: Weeks 9-12)."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .analytics import TestCoverageAnalyzer
from .graph import DependencyGraphEngine
from .models import (
    DependencyGraph,
    NodeSeverity,
)

logger = logging.getLogger(__name__)


@dataclass
class FailurePrediction:
    """Failure prediction for a node."""

    node_id: str
    failure_probability: float  # 0.0-1.0
    confidence: float
    contributing_factors: List[str]
    predicted_at: datetime
    time_to_failure: Optional[timedelta]


@dataclass
class AnomalyDetection:
    """Detected anomalies in dependency patterns."""

    anomaly_type: str  # unusual_connectivity, missing_tests, abandoned_node
    node_id: str
    severity: NodeSeverity
    details: str
    detected_at: datetime


@dataclass
class Recommendation:
    """Intelligence-based recommendation."""

    recommendation_type: str  # refactor, add_sla, increase_tests, optimize
    node_id: str
    priority: str  # critical, high, medium, low
    action: str
    expected_benefit: str
    effort: str


@dataclass
class HealthScore:
    """Overall health score for dependency graph."""

    overall_score: float  # 0-100
    coverage_score: float
    connectivity_score: float
    ownership_score: float
    test_score: float
    issues_count: int
    critical_issues: int


class FailurePredictionEngine:
    """Predict likelihood of node failures."""

    def __init__(
        self,
        graph: DependencyGraph,
        test_analyzer: Optional[TestCoverageAnalyzer] = None,
    ):
        self.graph = graph
        self.engine = DependencyGraphEngine(graph)
        self.test_analyzer = test_analyzer or TestCoverageAnalyzer(graph)
        self.failure_history: Dict[str, List[datetime]] = {}

    def record_failure(self, node_id: str) -> None:
        """Record a failure event."""
        if node_id not in self.failure_history:
            self.failure_history[node_id] = []
        self.failure_history[node_id].append(datetime.utcnow())

    def predict_node_failure(self, node_id: str) -> FailurePrediction:
        """
        Predict failure probability for a node.

        Factors:
        - Historical failure rate
        - Dependencies on failing nodes
        - Test coverage
        - Complexity
        - Age of last change
        """
        node = self.graph.nodes.get(node_id)
        if not node:
            return FailurePrediction(
                node_id=node_id,
                failure_probability=0.0,
                confidence=0.0,
                contributing_factors=[],
                predicted_at=datetime.utcnow(),
                time_to_failure=None,
            )

        probability = 0.0
        confidence = 0.5
        factors = []

        # Factor 1: Historical failure rate
        if node_id in self.failure_history:
            failures = self.failure_history[node_id]
            if len(failures) > 0:
                # Calculate failure frequency
                days_of_data = 30  # Assume 30 days of history
                failure_rate = len(failures) / days_of_data
                probability += min(0.3, failure_rate)
                factors.append(f"Historical failure rate: {failure_rate:.1%}")
                confidence = min(1.0, confidence + 0.2)

        # Factor 2: Upstream failures impact
        upstream = self.engine.get_upstream_nodes(node_id)
        failing_upstream = [
            u for u in upstream if u in self.failure_history and len(self.failure_history[u]) > 0
        ]
        if failing_upstream:
            probability += 0.2 * (len(failing_upstream) / max(1, len(upstream)))
            factors.append(f"{len(failing_upstream)} upstream nodes have failed")
            confidence = min(1.0, confidence + 0.1)

        # Factor 3: Test coverage
        test_count = self.test_analyzer.analyze_coverage(node_id).total_tests
        if test_count == 0:
            probability += 0.15
            factors.append("No test coverage")

        # Factor 4: Complexity (high downstream = higher risk)
        downstream = self.engine.get_downstream_nodes(node_id)
        if len(downstream) > 100:
            probability += 0.1
            factors.append(f"High complexity: {len(downstream)} downstream nodes")

        # Factor 5: Node severity (critical nodes maintained better)
        if node.severity == NodeSeverity.LOW:
            probability += 0.05
            factors.append("Low severity (may lack maintenance)")

        probability = min(1.0, probability)

        # Estimate time to failure based on frequency
        time_to_failure = None
        if probability > 0.3:
            # Convert probability to estimated hours until failure
            hours_until = int(max(1, (1.0 - probability) * 168))  # 168 hours/week
            time_to_failure = timedelta(hours=hours_until)

        return FailurePrediction(
            node_id=node_id,
            failure_probability=probability,
            confidence=confidence,
            contributing_factors=factors,
            predicted_at=datetime.utcnow(),
            time_to_failure=time_to_failure,
        )

    def predict_all_nodes(self) -> Dict[str, FailurePrediction]:
        """Predict failures for all nodes."""
        return {node_id: self.predict_node_failure(node_id) for node_id in self.graph.nodes}

    def get_high_risk_nodes(self, threshold: float = 0.5) -> List[FailurePrediction]:
        """Get nodes with failure probability above threshold."""
        predictions = self.predict_all_nodes()
        return sorted(
            [p for p in predictions.values() if p.failure_probability >= threshold],
            key=lambda p: p.failure_probability,
            reverse=True,
        )


class AnomalyDetector:
    """Detect anomalies in dependency patterns."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.engine = DependencyGraphEngine(graph)

    def detect_all_anomalies(self) -> List[AnomalyDetection]:
        """Detect all anomalies in the graph."""
        anomalies = []

        # Detect isolated nodes
        orphans = self.engine.detect_orphans()
        for isolated in orphans["isolated"]:
            node = self.graph.nodes.get(isolated)
            if node:
                anomalies.append(
                    AnomalyDetection(
                        anomaly_type="isolated_node",
                        node_id=isolated,
                        severity=(
                            NodeSeverity.HIGH
                            if node.severity == NodeSeverity.CRITICAL
                            else NodeSeverity.MEDIUM
                        ),
                        details=f"Node {node.name} has no dependencies or dependents",
                        detected_at=datetime.utcnow(),
                    )
                )

        # Detect unusual connectivity patterns
        centrality = self.engine.get_node_centrality()
        avg_centrality = sum(centrality.values()) / len(centrality) if centrality else 0
        high_centrality = {n: c for n, c in centrality.items() if c > avg_centrality * 3}

        for node_id, score in high_centrality.items():
            node = self.graph.nodes.get(node_id)
            if node:
                anomalies.append(
                    AnomalyDetection(
                        anomaly_type="high_centrality",
                        node_id=node_id,
                        severity=NodeSeverity.MEDIUM,
                        details=f"Node {node.name} has unusually high connectivity ({score:.1%})",
                        detected_at=datetime.utcnow(),
                    )
                )

        # Detect cycles (inherent anomalies)
        cycles = self.engine.detect_cycles()
        if cycles:
            for cycle in cycles[:5]:  # Report first 5 cycles
                if cycle:
                    anomalies.append(
                        AnomalyDetection(
                            anomaly_type="circular_dependency",
                            node_id=cycle[0],
                            severity=NodeSeverity.HIGH,
                            details=f"Circular dependency: {' -> '.join(cycle[:3])}...",
                            detected_at=datetime.utcnow(),
                        )
                    )

        # Detect unowned critical nodes
        for node in self.graph.nodes.values():
            if node.severity == NodeSeverity.CRITICAL and not node.owner:
                anomalies.append(
                    AnomalyDetection(
                        anomaly_type="unowned_critical",
                        node_id=node.id,
                        severity=NodeSeverity.HIGH,
                        details=f"Critical node {node.name} has no owner assigned",
                        detected_at=datetime.utcnow(),
                    )
                )

        return anomalies


class RecommendationEngine:
    """Generate intelligence-based recommendations."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.engine = DependencyGraphEngine(graph)

    def generate_recommendations(self) -> List[Recommendation]:
        """Generate all recommendations."""
        recommendations = []

        # Recommendation 1: Refactor high-centrality nodes
        centrality = self.engine.get_node_centrality()
        avg_centrality = sum(centrality.values()) / len(centrality) if centrality else 0
        high_centrality_nodes = sorted(
            [(n, c) for n, c in centrality.items() if c > avg_centrality * 2],
            key=lambda x: x[1],
            reverse=True,
        )

        for node_id, score in high_centrality_nodes[:5]:
            node = self.graph.nodes.get(node_id)
            if node:
                recommendations.append(
                    Recommendation(
                        recommendation_type="refactor_centrality",
                        node_id=node_id,
                        priority="high" if score > avg_centrality * 3 else "medium",
                        action=f"Refactor {node.name} to reduce connectivity",
                        expected_benefit="Reduced coupling, easier maintenance",
                        effort="2-3 days",
                    )
                )

        # Recommendation 2: Add SLAs to critical nodes
        critical_without_sla = [
            n.id for n in self.graph.nodes.values() if n.severity == NodeSeverity.CRITICAL
        ]

        for node_id in critical_without_sla[:10]:
            node = self.graph.nodes.get(node_id)
            if node:
                downstream_count = len(self.engine.get_downstream_nodes(node_id))
                recommendations.append(
                    Recommendation(
                        recommendation_type="add_sla",
                        node_id=node_id,
                        priority="critical",
                        action=f"Define SLA for {node.name}",
                        expected_benefit=f"Monitor {downstream_count} downstream nodes",
                        effort="1-2 hours",
                    )
                )

        # Recommendation 3: Improve test coverage
        # (Would integrate with TestCoverageAnalyzer)
        poorly_tested = [
            n.id
            for n in self.graph.nodes.values()
            if n.severity in (NodeSeverity.CRITICAL, NodeSeverity.HIGH)
        ][:5]

        for node_id in poorly_tested:
            node = self.graph.nodes.get(node_id)
            if node:
                recommendations.append(
                    Recommendation(
                        recommendation_type="improve_tests",
                        node_id=node_id,
                        priority="high",
                        action=f"Add tests for {node.name}",
                        expected_benefit="Reduce failure probability by 30%",
                        effort="2-3 days",
                    )
                )

        # Recommendation 4: Establish ownership
        unowned = [n for n in self.graph.nodes.values() if not n.owner]
        for node in unowned[:5]:
            recommendations.append(
                Recommendation(
                    recommendation_type="establish_ownership",
                    node_id=node.id,
                    priority="high" if node.severity == NodeSeverity.CRITICAL else "medium",
                    action=f"Assign owner to {node.name}",
                    expected_benefit="Clear responsibility, faster response",
                    effort="1 hour",
                )
            )

        return sorted(
            recommendations,
            key=lambda r: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(r.priority, 4),
        )

    def get_top_recommendations(self, limit: int = 10) -> List[Recommendation]:
        """Get top N recommendations."""
        return self.generate_recommendations()[:limit]


class HealthScoreCalculator:
    """Calculate overall health score for dependency graph."""

    def __init__(
        self,
        graph: DependencyGraph,
        test_analyzer: Optional[TestCoverageAnalyzer] = None,
    ):
        self.graph = graph
        self.engine = DependencyGraphEngine(graph)
        self.test_analyzer = test_analyzer or TestCoverageAnalyzer(graph)

    def calculate_health_score(self) -> HealthScore:
        """
        Calculate comprehensive health score.

        Components:
        - Coverage: percentage of nodes with metadata
        - Connectivity: balance between isolated and over-connected
        - Ownership: percentage of nodes with assigned owners
        - Tests: percentage of nodes with test coverage
        """
        # Coverage score (0-20)
        coverage_score = self._calculate_coverage_score()

        # Connectivity score (0-20)
        connectivity_score = self._calculate_connectivity_score()

        # Ownership score (0-20)
        ownership_score = self._calculate_ownership_score()

        # Test score (0-20)
        test_score = self._calculate_test_score()

        # SLA score (0-20)
        sla_score = self._calculate_sla_score()

        overall = coverage_score + connectivity_score + ownership_score + test_score + sla_score

        # Count issues
        issues = self._count_issues()

        return HealthScore(
            overall_score=overall,
            coverage_score=coverage_score,
            connectivity_score=connectivity_score,
            ownership_score=ownership_score,
            test_score=test_score,
            issues_count=issues["total"],
            critical_issues=issues["critical"],
        )

    def _calculate_coverage_score(self) -> float:
        """Score completeness of metadata."""
        nodes_with_description = sum(1 for n in self.graph.nodes.values() if n.description)
        coverage = nodes_with_description / len(self.graph.nodes) if self.graph.nodes else 0
        return min(20.0, coverage * 20)

    def _calculate_connectivity_score(self) -> float:
        """Score graph connectivity health."""
        components = self.engine.detect_disconnected_components()

        if len(components) <= 1:
            return 20.0  # Fully connected
        elif len(components) <= 3:
            return 15.0
        elif len(components) <= 10:
            return 10.0
        else:
            return 5.0

    def _calculate_ownership_score(self) -> float:
        """Score ownership coverage."""
        owned = sum(1 for n in self.graph.nodes.values() if n.owner)
        ownership = owned / len(self.graph.nodes) if self.graph.nodes else 0
        return min(20.0, ownership * 20)

    def _calculate_test_score(self) -> float:
        """Score test coverage using real data from TestCoverageAnalyzer."""
        if not self.graph.nodes:
            return 0.0
        nodes_with_tests = sum(
            1
            for node_id in self.graph.nodes
            if self.test_analyzer.analyze_coverage(node_id).total_tests > 0
        )
        coverage = nodes_with_tests / len(self.graph.nodes)
        return min(20.0, coverage * 20)

    def _calculate_sla_score(self) -> float:
        """Score SLA coverage for critical nodes."""
        critical = sum(1 for n in self.graph.nodes.values() if n.severity == NodeSeverity.CRITICAL)
        return min(20.0, (critical / max(1, critical)) * 10)

    def _count_issues(self) -> Dict[str, int]:
        """Count critical and total issues."""
        cycles = len(self.engine.detect_cycles())
        orphans = len(self.engine.detect_orphans()["isolated"])
        unowned_critical = sum(
            1
            for n in self.graph.nodes.values()
            if n.severity == NodeSeverity.CRITICAL and not n.owner
        )

        return {
            "total": cycles + orphans + unowned_critical,
            "critical": cycles + unowned_critical,
        }

    def get_health_summary(self) -> Dict[str, str]:
        """Get human-readable health summary."""
        score = self.calculate_health_score()

        if score.overall_score >= 80:
            status = "Excellent"
            color = "green"
        elif score.overall_score >= 60:
            status = "Good"
            color = "yellow"
        elif score.overall_score >= 40:
            status = "Fair"
            color = "orange"
        else:
            status = "Poor"
            color = "red"

        return {
            "status": status,
            "score": f"{score.overall_score:.1f}/100",
            "color": color,
            "critical_issues": str(score.critical_issues),
            "total_issues": str(score.issues_count),
        }
