"""Analysis engines for dependency intelligence."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from .graph import DependencyGraphEngine
from .models import (
    BlastRadiusResult,
    DependencyGraph,
    DriftDetectionResult,
    ImpactResult,
    Node,
    NodeSeverity,
    NodeType,
    RiskScoreResult,
)

logger = logging.getLogger(__name__)


class ImpactAnalysisEngine:
    """Analyze impact of changing a node on downstream dependencies."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.engine = DependencyGraphEngine(graph)

    def analyze(self, node_id: str, max_depth: Optional[int] = None) -> ImpactResult:
        """
        Analyze impact of changing a node.

        Args:
            node_id: Node to analyze
            max_depth: Maximum traversal depth

        Returns:
            ImpactResult with affected nodes and metrics
        """
        if node_id not in self.graph.nodes:
            return ImpactResult(
                node_id=node_id,
                impacted_nodes=[],
                impact_depth=0,
                impact_score=0.0,
            )

        # Get all downstream nodes
        downstream = self.engine.get_downstream_nodes(node_id, max_depth)

        # Calculate impact score based on criticality
        impact_score = self._calculate_impact_score(downstream)

        # Group by severity and type
        by_severity = self._group_by_severity(downstream)
        by_type = self._group_by_type(downstream)

        # Calculate depth
        depth = self._calculate_max_depth(node_id, downstream)

        return ImpactResult(
            node_id=node_id,
            impacted_nodes=downstream,
            impact_depth=depth,
            impact_score=impact_score,
            by_severity=by_severity,
            by_type=by_type,
            metadata={
                "total_impacted": len(downstream),
                "analyzed_at": datetime.utcnow().isoformat(),
            },
        )

    def _calculate_impact_score(self, nodes: List[str]) -> float:
        """Calculate impact score 0.0-1.0 based on criticality."""
        if not nodes:
            return 0.0

        critical_count = sum(
            1 for n in nodes
            if self.graph.nodes.get(n, Node("", "", NodeType.TASK)).severity
            == NodeSeverity.CRITICAL
        )

        return min(1.0, critical_count / len(nodes))

    def _group_by_severity(self, nodes: List[str]) -> Dict[NodeSeverity, List[str]]:
        """Group nodes by severity."""
        result = {}
        for severity in NodeSeverity:
            result[severity] = [
                n for n in nodes
                if self.graph.nodes.get(n, Node("", "", NodeType.TASK)).severity == severity
            ]
        return {k: v for k, v in result.items() if v}

    def _group_by_type(self, nodes: List[str]) -> Dict[NodeType, List[str]]:
        """Group nodes by type."""
        result = {}
        for node_type in NodeType:
            result[node_type] = [
                n for n in nodes
                if self.graph.nodes.get(n, Node("", "", NodeType.TASK)).type == node_type
            ]
        return {k: v for k, v in result.items() if v}

    def _calculate_max_depth(self, source: str, nodes: List[str]) -> int:
        """Calculate maximum depth to any impacted node."""
        if not nodes:
            return 0

        max_d = 0
        for node_id in nodes:
            path = self.engine.get_path(source, node_id)
            if path:
                max_d = max(max_d, len(path) - 1)

        return max_d


class BlastRadiusEngine:
    """Analyze blast radius of changes."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.engine = DependencyGraphEngine(graph)

    def analyze(self, change_nodes: List[str]) -> BlastRadiusResult:
        """
        Analyze blast radius of multiple node changes.

        Args:
            change_nodes: List of nodes that changed

        Returns:
            BlastRadiusResult with affected nodes and risk assessment
        """
        # Get all affected nodes (union of downstream)
        affected = set()
        for node_id in change_nodes:
            affected.update(self.engine.get_downstream_nodes(node_id))

        # Calculate severity distribution
        severity_dist = self._calculate_severity_distribution(list(affected))

        # Determine risk level
        risk_level = self._assess_risk_level(list(affected), severity_dist)

        # Check if deployment is safe
        deployable = self._is_deployable(list(affected), risk_level)

        # Calculate blast depth
        blast_depth = self._calculate_blast_depth(change_nodes, list(affected))

        return BlastRadiusResult(
            change_nodes=change_nodes,
            affected_nodes=list(affected),
            blast_radius=len(affected),
            blast_depth=blast_depth,
            severity_distribution=severity_dist,
            risk_level=risk_level,
            deployable=deployable,
            metadata={
                "analyzed_at": datetime.utcnow().isoformat(),
                "change_count": len(change_nodes),
            },
        )

    def _calculate_severity_distribution(self, nodes: List[str]) -> Dict[NodeSeverity, int]:
        """Calculate distribution of node severities."""
        dist = {s: 0 for s in NodeSeverity}
        for node_id in nodes:
            node = self.graph.nodes.get(node_id)
            if node:
                dist[node.severity] += 1
        return {k: v for k, v in dist.items() if v > 0}

    def _assess_risk_level(self, nodes: List[str], severity_dist: Dict[NodeSeverity, int]) -> str:
        """Assess risk level based on affected nodes."""
        if severity_dist.get(NodeSeverity.CRITICAL, 0) > 0:
            return "critical"
        elif severity_dist.get(NodeSeverity.HIGH, 0) > 3:
            return "high"
        elif severity_dist.get(NodeSeverity.MEDIUM, 0) > 10:
            return "medium"
        else:
            return "low"

    def _is_deployable(self, nodes: List[str], risk_level: str) -> bool:
        """Determine if changes are safe to deploy."""
        return risk_level not in ("critical", "high")

    def _calculate_blast_depth(self, change_nodes: List[str], affected: List[str]) -> int:
        """Calculate maximum depth of blast."""
        if not affected:
            return 0

        max_depth = 0
        for change_node in change_nodes:
            for affected_node in affected:
                path = self.engine.get_path(change_node, affected_node)
                if path:
                    max_depth = max(max_depth, len(path) - 1)

        return max_depth


class RiskScoringEngine:
    """Calculate risk scores for nodes based on criticality and dependencies."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.engine = DependencyGraphEngine(graph)

    def score_node(self, node_id: str) -> RiskScoreResult:
        """
        Calculate risk score for a node.

        Risk factors:
        - Severity (0-2 points)
        - Downstream count (0-3 points)
        - Upstream count (0-2 points)
        - Critical dependents (0-3 points)

        Returns:
            RiskScoreResult with score and breakdown
        """
        node = self.graph.nodes.get(node_id)
        if not node:
            return RiskScoreResult(
                node_id=node_id,
                risk_score=0.0,
                components={},
                factors=[],
                severity=NodeSeverity.LOW,
            )

        components = {}
        factors = []

        # Severity score (0-2)
        severity_scores = {
            NodeSeverity.CRITICAL: 2.0,
            NodeSeverity.HIGH: 1.5,
            NodeSeverity.MEDIUM: 1.0,
            NodeSeverity.LOW: 0.5,
        }
        components["severity"] = severity_scores.get(node.severity, 0.0)
        if node.severity in (NodeSeverity.CRITICAL, NodeSeverity.HIGH):
            factors.append(f"High severity: {node.severity.value}")

        # Downstream impact (0-3)
        downstream = self.engine.get_downstream_nodes(node_id)
        downstream_score = min(3.0, len(downstream) / 10.0)
        components["downstream"] = downstream_score
        if len(downstream) > 50:
            factors.append(f"High downstream impact: {len(downstream)} nodes")

        # Upstream criticality (0-2)
        upstream = self.engine.get_upstream_nodes(node_id)
        critical_upstream = sum(
            1 for u in upstream
            if self.graph.nodes.get(u, Node("", "", NodeType.TASK)).severity
            == NodeSeverity.CRITICAL
        )
        upstream_score = min(2.0, critical_upstream / 5.0)
        components["upstream"] = upstream_score
        if critical_upstream > 0:
            factors.append(f"Depends on {critical_upstream} critical upstream nodes")

        # Critical dependents (0-3)
        critical_downstream = sum(
            1 for d in downstream
            if self.graph.nodes.get(d, Node("", "", NodeType.TASK)).severity
            == NodeSeverity.CRITICAL
        )
        critical_score = min(3.0, critical_downstream / 5.0)
        components["critical_dependents"] = critical_score
        if critical_downstream > 0:
            factors.append(f"Has {critical_downstream} critical downstream nodes")

        # Cycle involvement
        cycles = self.engine.detect_cycles()
        in_cycle = any(node_id in cycle for cycle in cycles)
        cycle_score = 2.0 if in_cycle else 0.0
        components["in_cycle"] = cycle_score
        if in_cycle:
            factors.append("Node is part of a circular dependency")

        # Calculate total score (0-10)
        total_score = sum(components.values())
        risk_score = min(10.0, total_score)

        return RiskScoreResult(
            node_id=node_id,
            risk_score=risk_score,
            components=components,
            factors=factors,
            severity=self._score_to_severity(risk_score),
            metadata={
                "calculated_at": datetime.utcnow().isoformat(),
                "upstream_nodes": len(upstream),
                "downstream_nodes": len(downstream),
            },
        )

    def _score_to_severity(self, score: float) -> NodeSeverity:
        """Convert risk score to severity level."""
        if score >= 8.0:
            return NodeSeverity.CRITICAL
        elif score >= 6.0:
            return NodeSeverity.HIGH
        elif score >= 3.0:
            return NodeSeverity.MEDIUM
        else:
            return NodeSeverity.LOW

    def score_all_nodes(self) -> Dict[str, RiskScoreResult]:
        """Calculate risk scores for all nodes."""
        return {
            node_id: self.score_node(node_id)
            for node_id in self.graph.nodes
        }


class DriftDetectionEngine:
    """Detect changes in dependencies (drift detection)."""

    def __init__(self, current_graph: DependencyGraph, previous_graph: Optional[DependencyGraph] = None):
        self.current_graph = current_graph
        self.previous_graph = previous_graph or DependencyGraph()

    def detect_drift(self) -> DriftDetectionResult:
        """
        Detect dependency drift between current and previous graphs.

        Returns:
            DriftDetectionResult with detected changes
        """
        drifts = []
        affected_nodes = set()
        details = []

        # Detect added nodes
        added_nodes = set(self.current_graph.nodes.keys()) - set(self.previous_graph.nodes.keys())
        if added_nodes:
            drifts.append({
                "type": "nodes_added",
                "count": len(added_nodes),
                "nodes": list(added_nodes),
            })
            affected_nodes.update(added_nodes)
            details.append(f"Added {len(added_nodes)} new nodes")

        # Detect removed nodes
        removed_nodes = set(self.previous_graph.nodes.keys()) - set(self.current_graph.nodes.keys())
        if removed_nodes:
            drifts.append({
                "type": "nodes_removed",
                "count": len(removed_nodes),
                "nodes": list(removed_nodes),
            })
            affected_nodes.update(removed_nodes)
            details.append(f"Removed {len(removed_nodes)} nodes")

        # Detect added edges
        prev_edges = {(e.source, e.target) for e in self.previous_graph.edges}
        curr_edges = {(e.source, e.target) for e in self.current_graph.edges}
        added_edges = curr_edges - prev_edges

        if added_edges:
            drifts.append({
                "type": "edges_added",
                "count": len(added_edges),
                "edges": [{"source": s, "target": t} for s, t in sorted(added_edges)],
            })
            for source, target in added_edges:
                affected_nodes.add(source)
                affected_nodes.add(target)
            details.append(f"Added {len(added_edges)} new dependencies")

        # Detect removed edges
        removed_edges = prev_edges - curr_edges
        if removed_edges:
            drifts.append({
                "type": "edges_removed",
                "count": len(removed_edges),
                "edges": [{"source": s, "target": t} for s, t in sorted(removed_edges)],
            })
            for source, target in removed_edges:
                affected_nodes.add(source)
                affected_nodes.add(target)
            details.append(f"Removed {len(removed_edges)} dependencies")

        # Determine severity based on drift
        drift_count = len(drifts)
        if drift_count == 0:
            severity = NodeSeverity.LOW
        elif added_edges or removed_edges:
            # Edge changes are more significant than node changes
            severity = NodeSeverity.HIGH
        elif removed_nodes:
            # Removed nodes are concerning
            severity = NodeSeverity.MEDIUM
        else:
            severity = NodeSeverity.LOW

        return DriftDetectionResult(
            detected_drifts=drifts,
            drift_count=drift_count,
            affected_nodes=list(affected_nodes),
            severity=severity,
            details=details,
            metadata={
                "detected_at": datetime.utcnow().isoformat(),
                "previous_nodes": len(self.previous_graph.nodes),
                "current_nodes": len(self.current_graph.nodes),
                "previous_edges": len(self.previous_graph.edges),
                "current_edges": len(self.current_graph.edges),
            },
        )
