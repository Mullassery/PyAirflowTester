"""Data models for Dependency Intelligence Engine."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Optional, Any
from datetime import datetime


class NodeType(Enum):
    """Types of nodes in dependency graph."""
    DAG = "dag"
    TASK = "task"
    TASK_GROUP = "task_group"
    DATASET = "dataset"
    DBT_SOURCE = "dbt_source"
    DBT_MODEL = "dbt_model"
    DBT_TEST = "dbt_test"
    DBT_SNAPSHOT = "dbt_snapshot"
    DBT_EXPOSURE = "dbt_exposure"
    EXTERNAL_TABLE = "external_table"
    EXTERNAL_API = "external_api"
    DASHBOARD = "dashboard"


class NodeSeverity(Enum):
    """Severity levels for nodes."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RelationshipType(Enum):
    """Types of edges/relationships."""
    DEPENDS_ON = "depends_on"
    TRIGGERS = "triggers"
    DATASET_CONSUMER = "dataset_consumer"
    DATASET_PRODUCER = "dataset_producer"
    TEST_OF = "test_of"
    EXPOSES = "exposes"
    CALLS = "calls"


@dataclass
class Node:
    """Represents a node in the dependency graph."""
    id: str
    name: str
    type: NodeType
    owner: str = ""
    severity: NodeSeverity = NodeSeverity.MEDIUM
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Cached computed properties
    upstream_count: int = 0
    downstream_count: int = 0
    upstream_nodes: Set[str] = field(default_factory=set)
    downstream_nodes: Set[str] = field(default_factory=set)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.id == other.id


@dataclass
class Edge:
    """Represents an edge/relationship between nodes."""
    source: str
    target: str
    relationship_type: RelationshipType = RelationshipType.DEPENDS_ON
    strength: float = 1.0  # 0.0-1.0, indicates importance/weight
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __hash__(self):
        return hash((self.source, self.target, self.relationship_type))

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return (self.source == other.source and
                self.target == other.target and
                self.relationship_type == other.relationship_type)


@dataclass
class DependencyGraph:
    """Represents complete dependency graph."""
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        self.updated_at = datetime.utcnow()

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)

        # Update node counts
        if edge.source in self.nodes:
            self.nodes[edge.source].downstream_nodes.add(edge.target)
            self.nodes[edge.source].downstream_count += 1

        if edge.target in self.nodes:
            self.nodes[edge.target].upstream_nodes.add(edge.source)
            self.nodes[edge.target].upstream_count += 1

        self.updated_at = datetime.utcnow()

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def get_edges_from(self, source_id: str) -> List[Edge]:
        """Get all outgoing edges from a node."""
        return [e for e in self.edges if e.source == source_id]

    def get_edges_to(self, target_id: str) -> List[Edge]:
        """Get all incoming edges to a node."""
        return [e for e in self.edges if e.target == target_id]

    def get_node_count_by_type(self) -> Dict[NodeType, int]:
        """Count nodes by type."""
        counts = {}
        for node in self.nodes.values():
            counts[node.type] = counts.get(node.type, 0) + 1
        return counts

    def get_critical_nodes(self) -> List[Node]:
        """Get all critical severity nodes."""
        return [n for n in self.nodes.values()
                if n.severity == NodeSeverity.CRITICAL]

    def stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "node_types": self.get_node_count_by_type(),
            "critical_nodes": len(self.get_critical_nodes()),
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# Analysis result dataclasses

@dataclass
class ImpactResult:
    """Result of impact analysis."""
    node_id: str
    impacted_nodes: List[str]
    impact_depth: int
    impact_score: float  # 0.0-1.0
    by_severity: Dict[NodeSeverity, List[str]] = field(default_factory=dict)
    by_type: Dict[NodeType, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BlastRadiusResult:
    """Result of blast radius analysis."""
    change_nodes: List[str]
    affected_nodes: List[str]
    blast_radius: int  # Number of affected nodes
    blast_depth: int  # Max depth of impact
    severity_distribution: Dict[NodeSeverity, int] = field(default_factory=dict)
    risk_level: str = "low"  # low, medium, high, critical
    deployable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskScoreResult:
    """Result of risk scoring."""
    node_id: str
    risk_score: float  # 0.0-10.0
    components: Dict[str, float] = field(default_factory=dict)
    factors: List[str] = field(default_factory=list)
    severity: NodeSeverity = NodeSeverity.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DriftDetectionResult:
    """Result of drift detection analysis."""
    detected_drifts: List[Dict[str, Any]] = field(default_factory=list)
    drift_count: int = 0
    affected_nodes: List[str] = field(default_factory=list)
    severity: NodeSeverity = NodeSeverity.LOW
    details: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
