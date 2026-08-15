"""Dependency Intelligence Engine for PyAirflowTester."""

from .analytics import (
    OwnershipAnalysis,
    OwnershipAnalyzer,
    SchemaEvolution,
    SchemaEvolutionTracker,
    SLAValidation,
    SLAValidator,
    TestCoverageAnalysis,
    TestCoverageAnalyzer,
)
from .analyzers import (
    BlastRadiusEngine,
    DriftDetectionEngine,
    ImpactAnalysisEngine,
    RiskScoringEngine,
)
from .graph import DependencyGraphEngine
from .intelligence import (
    AnomalyDetection,
    AnomalyDetector,
    FailurePrediction,
    FailurePredictionEngine,
    HealthScore,
    HealthScoreCalculator,
    Recommendation,
    RecommendationEngine,
)
from .models import (
    BlastRadiusResult,
    DependencyGraph,
    DriftDetectionResult,
    Edge,
    ImpactResult,
    Node,
    NodeSeverity,
    NodeType,
    RiskScoreResult,
)
from .observability import (
    Alert,
    AlertManager,
    DashboardBuilder,
    EventLogger,
    ExecutionEvent,
    Metric,
    MetricsCollector,
    MetricType,
)
from .parsers import (
    AirflowDAGParser,
    AirflowDatasetParser,
    UnifiedGraphBuilder,
    dbtManifestParser,
)

__all__ = [
    # Models
    "NodeType",
    "NodeSeverity",
    "Node",
    "Edge",
    "DependencyGraph",
    "ImpactResult",
    "BlastRadiusResult",
    "RiskScoreResult",
    "DriftDetectionResult",
    # Graph
    "DependencyGraphEngine",
    # Parsers
    "AirflowDAGParser",
    "dbtManifestParser",
    "AirflowDatasetParser",
    "UnifiedGraphBuilder",
    # Phase 1 Analyzers
    "ImpactAnalysisEngine",
    "BlastRadiusEngine",
    "RiskScoringEngine",
    "DriftDetectionEngine",
    # Phase 2 Analytics
    "OwnershipAnalyzer",
    "SchemaEvolutionTracker",
    "SLAValidator",
    "TestCoverageAnalyzer",
    "OwnershipAnalysis",
    "SchemaEvolution",
    "SLAValidation",
    "TestCoverageAnalysis",
    # Phase 3 Intelligence
    "FailurePredictionEngine",
    "AnomalyDetector",
    "RecommendationEngine",
    "HealthScoreCalculator",
    "FailurePrediction",
    "AnomalyDetection",
    "Recommendation",
    "HealthScore",
    # Phase 4 Observability
    "MetricsCollector",
    "AlertManager",
    "EventLogger",
    "DashboardBuilder",
    "MetricType",
    "Metric",
    "Alert",
    "ExecutionEvent",
]

__version__ = "0.4.0"  # Phase 1-4 MVP complete
