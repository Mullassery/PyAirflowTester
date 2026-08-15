"""
Scoring and risk assessment module.
"""

from typing import Any, Dict, List

from pyairflowtester.models import SEVERITY_WEIGHTS


class Scorer:
    """Risk scoring engine."""

    def __init__(self):
        """Initialize scorer."""
        self.severity_weights = SEVERITY_WEIGHTS

    def calculate_risk_score(self, violations: List[Dict[str, Any]]) -> float:
        """
        Calculate risk score from violations (0-100).

        Args:
            violations: List of violations

        Returns:
            Risk score (0-100)
        """
        if not violations:
            return 100.0

        total_severity = sum(
            self.severity_weights.get(v.get("severity", "info"), 0)
            for v in violations
        )

        avg_severity = total_severity / len(violations)
        violation_count_factor = min(len(violations) / 10.0, 1.0)

        base_risk = (1.0 - avg_severity) * 100.0
        adjusted_risk = base_risk * (1.0 + violation_count_factor)

        return min(adjusted_risk, 100.0)

    def aggregate_by_severity(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Aggregate violations by severity.

        Args:
            violations: List of violations

        Returns:
            Aggregation by severity
        """
        aggregated = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

        for v in violations:
            severity = v.get("severity", "info")
            if severity in aggregated:
                aggregated[severity] += 1

        return aggregated

    def categorize_risk(self, score: float) -> str:
        """
        Categorize risk level.

        Args:
            score: Risk score (0-100)

        Returns:
            Risk level
        """
        if score <= 25.0:
            return "low"
        elif score <= 50.0:
            return "medium"
        elif score <= 75.0:
            return "high"
        else:
            return "critical"

    def calculate_health_score(
        self,
        reliability: float,
        performance: float,
        maintainability: float,
    ) -> float:
        """
        Calculate health score based on multiple dimensions.

        Args:
            reliability: Reliability score (0-100)
            performance: Performance score (0-100)
            maintainability: Maintainability score (0-100)

        Returns:
            Health score (0-100)
        """
        # Weighted average: reliability 50%, performance 30%, maintainability 20%
        score = (reliability * 0.5 + performance * 0.3 + maintainability * 0.2)
        return min(max(score, 0.0), 100.0)

    def calculate_trend(self, current_score: float, previous_score: float) -> str:
        """
        Calculate trend.

        Args:
            current_score: Current score
            previous_score: Previous score

        Returns:
            Trend (improving/stable/degrading)
        """
        diff = current_score - previous_score
        if diff > 5.0:
            return "improving"
        elif diff < -5.0:
            return "degrading"
        else:
            return "stable"

    def filter_by_severity(
        self,
        violations: List[Dict[str, Any]],
        min_severity: str,
    ) -> List[Dict[str, Any]]:
        """
        Filter violations by minimum severity.

        Args:
            violations: List of violations
            min_severity: Minimum severity level

        Returns:
            Filtered violations
        """
        min_weight = self.severity_weights.get(min_severity, 0)

        return [
            v for v in violations
            if self.severity_weights.get(v.get("severity", "info"), 0) >= min_weight
        ]
