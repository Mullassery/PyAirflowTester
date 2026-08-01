"""Tests for scoring module."""

import pytest
from pyairflowtester.scoring import Scorer


class TestScorer:
    """Scorer test suite."""

    @pytest.fixture
    def scorer(self):
        """Create scorer instance."""
        return Scorer()

    def test_scorer_initialization(self, scorer):
        """Test scorer initialization."""
        assert scorer is not None
        assert len(scorer.severity_weights) == 5

    def test_risk_score_no_violations(self, scorer):
        """Test risk score with no violations."""
        violations = []
        score = scorer.calculate_risk_score(violations)
        assert score == 100.0

    def test_risk_score_with_violations(self, scorer):
        """Test risk score with violations."""
        violations = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
        ]
        score = scorer.calculate_risk_score(violations)
        assert 0 <= score <= 100

    def test_aggregate_by_severity(self, scorer):
        """Test aggregation by severity."""
        violations = [
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
        ]
        aggregated = scorer.aggregate_by_severity(violations)
        assert aggregated["critical"] == 2
        assert aggregated["high"] == 1
        assert aggregated["medium"] == 1

    def test_categorize_risk_low(self, scorer):
        """Test risk categorization - low."""
        assert scorer.categorize_risk(10.0) == "low"
        assert scorer.categorize_risk(25.0) == "low"

    def test_categorize_risk_medium(self, scorer):
        """Test risk categorization - medium."""
        assert scorer.categorize_risk(40.0) == "medium"
        assert scorer.categorize_risk(50.0) == "medium"

    def test_categorize_risk_high(self, scorer):
        """Test risk categorization - high."""
        assert scorer.categorize_risk(60.0) == "high"
        assert scorer.categorize_risk(75.0) == "high"

    def test_categorize_risk_critical(self, scorer):
        """Test risk categorization - critical."""
        assert scorer.categorize_risk(85.0) == "critical"
        assert scorer.categorize_risk(100.0) == "critical"

    def test_calculate_health_score_perfect(self, scorer):
        """Test perfect health score."""
        health = scorer.calculate_health_score(100.0, 100.0, 100.0)
        assert health == 100.0

    def test_calculate_health_score_zero(self, scorer):
        """Test zero health score."""
        health = scorer.calculate_health_score(0.0, 0.0, 0.0)
        assert health == 0.0

    def test_calculate_health_score_weighted(self, scorer):
        """Test weighted health score."""
        # Reliability: 100 (50%), Performance: 0 (30%), Maintainability: 0 (20%)
        # Expected: 100 * 0.5 = 50
        health = scorer.calculate_health_score(100.0, 0.0, 0.0)
        assert health == 50.0

    def test_calculate_trend_improving(self, scorer):
        """Test trend calculation - improving."""
        trend = scorer.calculate_trend(80.0, 70.0)
        assert trend == "improving"

    def test_calculate_trend_degrading(self, scorer):
        """Test trend calculation - degrading."""
        trend = scorer.calculate_trend(70.0, 80.0)
        assert trend == "degrading"

    def test_calculate_trend_stable(self, scorer):
        """Test trend calculation - stable."""
        trend = scorer.calculate_trend(75.0, 75.0)
        assert trend == "stable"

    def test_filter_by_severity(self, scorer):
        """Test filtering by severity."""
        violations = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
        ]

        filtered = scorer.filter_by_severity(violations, "high")
        assert len(filtered) == 2  # critical and high
        assert all(v["severity"] in ["critical", "high"] for v in filtered)

    def test_filter_by_severity_all(self, scorer):
        """Test filtering with lowest severity."""
        violations = [
            {"severity": "critical"},
            {"severity": "medium"},
        ]

        filtered = scorer.filter_by_severity(violations, "info")
        assert len(filtered) == 2  # all
