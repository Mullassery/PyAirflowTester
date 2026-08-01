"""Observability and monitoring engines (Phase 4: Weeks 13-16)."""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from .models import Node, NodeSeverity, DependencyGraph

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to track."""
    EXECUTION_TIME = "execution_time"
    FAILURE_COUNT = "failure_count"
    DATA_VOLUME = "data_volume"
    RESOURCE_USAGE = "resource_usage"
    QUALITY_SCORE = "quality_score"


@dataclass
class Metric:
    """Individual metric observation."""
    metric_type: MetricType
    node_id: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]


@dataclass
class Alert:
    """Alert for detected issues."""
    alert_id: str
    alert_type: str  # threshold_exceeded, anomaly_detected, sla_violated
    node_id: str
    severity: NodeSeverity
    message: str
    metric_value: Optional[float]
    threshold: Optional[float]
    created_at: datetime
    resolved_at: Optional[datetime] = None


@dataclass
class ExecutionEvent:
    """Record of node execution."""
    event_id: str
    node_id: str
    status: str  # success, failure, timeout
    duration_ms: int
    start_time: datetime
    end_time: datetime
    error_message: Optional[str] = None
    tags: Dict[str, str] = None


class MetricsCollector:
    """Collect and aggregate metrics from nodes."""

    def __init__(self):
        self.metrics: List[Metric] = []
        self.retention_days = 30

    def record_metric(self, metric_type: MetricType, node_id: str,
                     value: float, tags: Dict[str, str] = None) -> Metric:
        """Record a metric observation."""
        metric = Metric(
            metric_type=metric_type,
            node_id=node_id,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {},
        )
        self.metrics.append(metric)
        return metric

    def get_metrics_for_node(self, node_id: str,
                            metric_type: Optional[MetricType] = None,
                            hours: int = 24) -> List[Metric]:
        """Get recent metrics for a node."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        return [
            m for m in self.metrics
            if m.node_id == node_id
            and m.timestamp >= cutoff
            and (metric_type is None or m.metric_type == metric_type)
        ]

    def calculate_statistics(self, node_id: str, metric_type: MetricType,
                            hours: int = 24) -> Dict[str, float]:
        """Calculate statistics for a metric."""
        metrics = self.get_metrics_for_node(node_id, metric_type, hours)

        if not metrics:
            return {
                "count": 0,
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p95": 0.0,
                "p99": 0.0,
            }

        values = sorted([m.value for m in metrics])
        count = len(values)

        return {
            "count": count,
            "min": float(min(values)),
            "max": float(max(values)),
            "avg": float(sum(values) / count),
            "p95": float(values[int(count * 0.95)]) if count > 0 else 0.0,
            "p99": float(values[int(count * 0.99)]) if count > 0 else 0.0,
        }

    def cleanup_old_metrics(self) -> int:
        """Remove metrics older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        old_count = len([m for m in self.metrics if m.timestamp < cutoff])

        self.metrics = [m for m in self.metrics if m.timestamp >= cutoff]
        return old_count


class AlertManager:
    """Manage alerts for threshold violations and anomalies."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.alerts: List[Alert] = []
        self.thresholds: Dict[str, Dict[str, float]] = {}

    def set_threshold(self, node_id: str, metric_type: str,
                     warning: float, critical: float) -> None:
        """Set threshold for a metric."""
        if node_id not in self.thresholds:
            self.thresholds[node_id] = {}

        self.thresholds[node_id][metric_type] = {
            "warning": warning,
            "critical": critical,
        }

    def check_threshold(self, node_id: str, metric_type: str,
                       value: float) -> Optional[Alert]:
        """Check if metric exceeds threshold."""
        if node_id not in self.thresholds:
            return None

        thresholds = self.thresholds[node_id].get(metric_type)
        if not thresholds:
            return None

        node = self.graph.nodes.get(node_id)
        if not node:
            return None

        alert = None
        if value > thresholds["critical"]:
            alert = Alert(
                alert_id=f"{node_id}_{metric_type}_{datetime.utcnow().timestamp()}",
                alert_type="threshold_exceeded",
                node_id=node_id,
                severity=NodeSeverity.CRITICAL,
                message=f"{metric_type} exceeded critical threshold",
                metric_value=value,
                threshold=thresholds["critical"],
                created_at=datetime.utcnow(),
            )
        elif value > thresholds["warning"]:
            alert = Alert(
                alert_id=f"{node_id}_{metric_type}_{datetime.utcnow().timestamp()}",
                alert_type="threshold_exceeded",
                node_id=node_id,
                severity=NodeSeverity.HIGH,
                message=f"{metric_type} exceeded warning threshold",
                metric_value=value,
                threshold=thresholds["warning"],
                created_at=datetime.utcnow(),
            )

        if alert:
            self.alerts.append(alert)

        return alert

    def get_active_alerts(self) -> List[Alert]:
        """Get unresolved alerts."""
        return [a for a in self.alerts if a.resolved_at is None]

    def resolve_alert(self, alert_id: str) -> None:
        """Mark alert as resolved."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved_at = datetime.utcnow()
                break

    def get_alerts_for_node(self, node_id: str) -> List[Alert]:
        """Get all alerts for a node."""
        return [a for a in self.alerts if a.node_id == node_id]


class EventLogger:
    """Log execution events for audit trail and analysis."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self.events: List[ExecutionEvent] = []
        self.retention_days = 90

    def log_execution(self, node_id: str, status: str, duration_ms: int,
                     start_time: datetime, end_time: datetime,
                     error_message: Optional[str] = None,
                     tags: Dict[str, str] = None) -> ExecutionEvent:
        """Log a node execution event."""
        event = ExecutionEvent(
            event_id=f"{node_id}_{start_time.timestamp()}",
            node_id=node_id,
            status=status,
            duration_ms=duration_ms,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
            tags=tags or {},
        )
        self.events.append(event)
        return event

    def get_events_for_node(self, node_id: str, hours: int = 24) -> List[ExecutionEvent]:
        """Get recent events for a node."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            e for e in self.events
            if e.node_id == node_id and e.start_time >= cutoff
        ]

    def get_failure_rate(self, node_id: str, hours: int = 24) -> float:
        """Calculate failure rate for a node."""
        events = self.get_events_for_node(node_id, hours)
        if not events:
            return 0.0

        failures = sum(1 for e in events if e.status == "failure")
        return failures / len(events)

    def get_average_duration(self, node_id: str, hours: int = 24) -> float:
        """Get average execution duration for a node."""
        events = self.get_events_for_node(node_id, hours)
        if not events:
            return 0.0

        successful = [e for e in events if e.status == "success"]
        if not successful:
            return 0.0

        return sum(e.duration_ms for e in successful) / len(successful)

    def cleanup_old_events(self) -> int:
        """Remove events older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        old_count = len([e for e in self.events if e.start_time < cutoff])

        self.events = [e for e in self.events if e.start_time >= cutoff]
        return old_count

    def export_events(self, node_id: Optional[str] = None) -> str:
        """Export events as JSON."""
        events = self.events
        if node_id:
            events = [e for e in events if e.node_id == node_id]

        # Convert to dictionaries, handling datetime
        events_dict = []
        for e in events:
            d = asdict(e)
            d['start_time'] = e.start_time.isoformat()
            d['end_time'] = e.end_time.isoformat()
            events_dict.append(d)

        return json.dumps(events_dict, indent=2)


class DashboardBuilder:
    """Build observability dashboards."""

    def __init__(self, graph: DependencyGraph, metrics_collector: MetricsCollector,
                 alert_manager: AlertManager, event_logger: EventLogger):
        self.graph = graph
        self.metrics = metrics_collector
        self.alerts = alert_manager
        self.events = event_logger

    def build_node_dashboard(self, node_id: str) -> Dict[str, Any]:
        """Build a dashboard for a specific node."""
        node = self.graph.nodes.get(node_id)
        if not node:
            return {}

        # Get metrics
        execution_times = self.metrics.get_metrics_for_node(
            node_id, MetricType.EXECUTION_TIME, hours=24
        )
        exec_stats = self.metrics.calculate_statistics(
            node_id, MetricType.EXECUTION_TIME, hours=24
        )

        # Get events
        events = self.events.get_events_for_node(node_id, hours=24)
        failure_rate = self.events.get_failure_rate(node_id)

        # Get alerts
        alerts = self.alerts.get_alerts_for_node(node_id)
        active_alerts = [a for a in alerts if a.resolved_at is None]

        return {
            "node_id": node_id,
            "node_name": node.name,
            "node_type": node.type.value,
            "severity": node.severity.value,
            "owner": node.owner,
            "dashboard": {
                "execution_metrics": {
                    "average_duration_ms": exec_stats.get("avg", 0),
                    "min_duration_ms": exec_stats.get("min", 0),
                    "max_duration_ms": exec_stats.get("max", 0),
                    "p95_duration_ms": exec_stats.get("p95", 0),
                    "recent_executions": len(execution_times),
                },
                "reliability": {
                    "failure_rate": f"{failure_rate:.1%}",
                    "successful_runs": len([e for e in events if e.status == "success"]),
                    "failed_runs": len([e for e in events if e.status == "failure"]),
                    "timeout_runs": len([e for e in events if e.status == "timeout"]),
                },
                "alerts": {
                    "active_count": len(active_alerts),
                    "critical": len([a for a in active_alerts if a.severity == NodeSeverity.CRITICAL]),
                    "high": len([a for a in active_alerts if a.severity == NodeSeverity.HIGH]),
                },
                "recent_events": [
                    {
                        "timestamp": e.start_time.isoformat(),
                        "status": e.status,
                        "duration_ms": e.duration_ms,
                        "error": e.error_message,
                    }
                    for e in events[-10:]  # Last 10 events
                ],
            },
        }

    def build_health_dashboard(self) -> Dict[str, Any]:
        """Build overall system health dashboard."""
        all_events = self.events.events
        all_alerts = self.alerts.get_active_alerts()

        # Calculate aggregate metrics
        total_executions = len(all_events)
        failed = len([e for e in all_events if e.status == "failure"])
        avg_failure_rate = failed / total_executions if total_executions > 0 else 0

        return {
            "dashboard": "System Health",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_nodes": len(self.graph.nodes),
                "total_edges": len(self.graph.edges),
            },
            "execution_stats": {
                "total_executions": total_executions,
                "successful": total_executions - failed,
                "failed": failed,
                "overall_failure_rate": f"{avg_failure_rate:.1%}",
            },
            "alerts": {
                "active_alerts": len(all_alerts),
                "critical": len([a for a in all_alerts if a.severity == NodeSeverity.CRITICAL]),
                "high": len([a for a in all_alerts if a.severity == NodeSeverity.HIGH]),
                "medium": len([a for a in all_alerts if a.severity == NodeSeverity.MEDIUM]),
            },
            "top_failing_nodes": self._get_top_failing_nodes(),
            "slowest_nodes": self._get_slowest_nodes(),
        }

    def _get_top_failing_nodes(self, limit: int = 5) -> List[Dict]:
        """Get nodes with highest failure rates."""
        node_failures = {}

        for node_id in self.graph.nodes:
            failure_rate = self.events.get_failure_rate(node_id)
            if failure_rate > 0:
                node_failures[node_id] = failure_rate

        top = sorted(node_failures.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [
            {
                "node_id": node_id,
                "node_name": self.graph.nodes[node_id].name,
                "failure_rate": f"{rate:.1%}",
            }
            for node_id, rate in top
        ]

    def _get_slowest_nodes(self, limit: int = 5) -> List[Dict]:
        """Get slowest executing nodes."""
        node_durations = {}

        for node_id in self.graph.nodes:
            avg_duration = self.events.get_average_duration(node_id)
            if avg_duration > 0:
                node_durations[node_id] = avg_duration

        top = sorted(node_durations.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [
            {
                "node_id": node_id,
                "node_name": self.graph.nodes[node_id].name,
                "average_duration_ms": int(duration),
            }
            for node_id, duration in top
        ]
