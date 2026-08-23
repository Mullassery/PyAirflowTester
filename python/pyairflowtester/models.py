"""
Data models for PyAirflowTester.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# Severity weights for scoring
SEVERITY_WEIGHTS = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.5,
    "low": 0.25,
    "info": 0.1,
}


@dataclass
class Rule:
    """Rule definition."""

    id: str
    name: str
    severity: str
    category: str
    execution_mode: str
    description: str
    remediation: str
    tags: List[str] = field(default_factory=list)


@dataclass
class RuleViolation:
    """Rule violation result."""

    rule_id: str
    severity: str
    affected_resource: str
    message: str
    remediation: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "affected_resource": self.affected_resource,
            "message": self.message,
            "remediation": self.remediation,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DagDefinition:
    """Airflow DAG definition."""

    dag_id: str
    file_path: str
    source_code: str
    parse_time_ms: float = 0.0
    task_count: int = 0
    task_ids: List[str] = field(default_factory=list)
    max_task_depth: int = 0
    has_cycles: bool = False
    dynamic_dag_detected: bool = False
    expensive_imports: List[str] = field(default_factory=list)
    external_dependencies: List[str] = field(default_factory=list)


@dataclass
class DbtModel:
    """dbt model definition."""

    name: str
    materialization: str = "table"
    description: str = ""
    columns: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    downstream_models: List[str] = field(default_factory=list)
    upstream_models: List[str] = field(default_factory=list)
    source_file: str = ""


@dataclass
class DbtTest:
    """dbt test definition."""

    name: str
    test_type: str
    model_name: str
    source_name: Optional[str] = None
    column_name: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)


@dataclass
class RiskScorecard:
    """Risk scorecard for a resource."""

    resource_id: str
    resource_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reliability_score: float = 75.0
    performance_score: float = 75.0
    maintainability_score: float = 75.0
    security_score: float = 75.0
    cost_efficiency_score: float = 75.0
    overall_health_score: float = 75.0
    risk_level: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "timestamp": self.timestamp.isoformat(),
            "reliability_score": self.reliability_score,
            "performance_score": self.performance_score,
            "maintainability_score": self.maintainability_score,
            "security_score": self.security_score,
            "cost_efficiency_score": self.cost_efficiency_score,
            "overall_health_score": self.overall_health_score,
            "risk_level": self.risk_level,
        }


@dataclass
class AnalysisContext:
    """Context for analysis."""

    dag_id: Optional[str] = None
    task_id: Optional[str] = None
    model_name: Optional[str] = None
    test_id: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
