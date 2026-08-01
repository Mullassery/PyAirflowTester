"""Dependency Intelligence Engine for PyAirflowTester."""

from .models import (
    NodeType,
    NodeSeverity,
    Node,
    Edge,
    DependencyGraph,
    ImpactResult,
    BlastRadiusResult,
    RiskScoreResult,
    DriftDetectionResult,
)
from .graph import DependencyGraphEngine
from .parsers import (
    AirflowDAGParser,
    dbtManifestParser,
    AirflowDatasetParser,
    UnifiedGraphBuilder,
)
from .analyzers import (
    ImpactAnalysisEngine,
    BlastRadiusEngine,
    RiskScoringEngine,
    DriftDetectionEngine,
)
from .analytics import (
    OwnershipAnalyzer,
    SchemaEvolutionTracker,
    SLAValidator,
    TestCoverageAnalyzer,
    OwnershipAnalysis,
    SchemaEvolution,
    SLAValidation,
    TestCoverageAnalysis,
)
from .intelligence import (
    FailurePredictionEngine,
    AnomalyDetector,
    RecommendationEngine,
    HealthScoreCalculator,
    FailurePrediction,
    AnomalyDetection,
    Recommendation,
    HealthScore,
)
from .observability import (
    MetricsCollector,
    AlertManager,
    EventLogger,
    DashboardBuilder,
    MetricType,
    Metric,
    Alert,
    ExecutionEvent,
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
