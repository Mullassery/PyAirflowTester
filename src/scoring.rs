use crate::rule_engine::{RuleViolation, Severity};
use std::collections::HashMap;

/// Scoring calculation engine
pub struct Scorer {
    severity_weights: HashMap<String, f64>,
}

impl Scorer {
    pub fn new() -> Self {
        let mut weights = HashMap::new();
        weights.insert("critical".to_string(), 1.0);
        weights.insert("high".to_string(), 0.75);
        weights.insert("medium".to_string(), 0.50);
        weights.insert("low".to_string(), 0.25);
        weights.insert("info".to_string(), 0.10);

        Scorer {
            severity_weights: weights,
        }
    }

    /// Calculate risk score from violations (0-100)
    pub fn calculate_risk_score(&self, violations: &[RuleViolation]) -> f64 {
        if violations.is_empty() {
            return 100.0;
        }

        let total_severity: f64 = violations
            .iter()
            .map(|v| self.severity_weights.get(v.severity.as_str()).unwrap_or(&0.0))
            .sum();

        let avg_severity = total_severity / violations.len() as f64;
        let violation_count_factor = ((violations.len() as f64) / 10.0).min(1.0);

        // Risk = (1 - average severity) * 100, adjusted for violation count
        let base_risk = (1.0 - avg_severity) * 100.0;
        let adjusted_risk = base_risk * (1.0 + violation_count_factor);

        adjusted_risk.min(100.0)
    }

    /// Aggregate violations by severity
    pub fn aggregate_by_severity(&self, violations: &[RuleViolation]) -> HashMap<String, usize> {
        let mut aggregated = HashMap::new();
        aggregated.insert("critical".to_string(), 0);
        aggregated.insert("high".to_string(), 0);
        aggregated.insert("medium".to_string(), 0);
        aggregated.insert("low".to_string(), 0);
        aggregated.insert("info".to_string(), 0);

        for violation in violations {
            let severity = violation.severity.as_str();
            *aggregated.entry(severity.to_string()).or_insert(0) += 1;
        }

        aggregated
    }

    /// Aggregate violations by category
    pub fn aggregate_by_category(&self, violations: &[RuleViolation]) -> HashMap<String, usize> {
        let mut aggregated: HashMap<String, usize> = HashMap::new();

        for violation in violations {
            *aggregated.entry(violation.rule_id.clone()).or_insert(0) += 1;
        }

        aggregated
    }

    /// Calculate priority score for violations
    pub fn calculate_priority_score(&self, violation: &RuleViolation) -> f64 {
        let severity_weight = self
            .severity_weights
            .get(violation.severity.as_str())
            .unwrap_or(&0.0);

        severity_weight * 100.0
    }

    /// Filter violations by minimum severity
    pub fn filter_by_severity(&self, violations: &[RuleViolation], min_severity: &str) -> Vec<RuleViolation> {
        let min_weight = self.severity_weights.get(min_severity).unwrap_or(&0.0);

        violations
            .iter()
            .filter(|v| {
                let v_weight = self.severity_weights.get(v.severity.as_str()).unwrap_or(&0.0);
                v_weight >= min_weight
            })
            .cloned()
            .collect()
    }

    /// Calculate health score based on multiple dimensions (0-100)
    pub fn calculate_health_score(
        &self,
        reliability: f64,
        performance: f64,
        maintainability: f64,
    ) -> f64 {
        // Weighted average: reliability 50%, performance 30%, maintainability 20%
        (reliability * 0.5 + performance * 0.3 + maintainability * 0.2).min(100.0).max(0.0)
    }

    /// Categorize risk level
    pub fn categorize_risk(&self, score: f64) -> String {
        match score {
            0.0..=25.0 => "low".to_string(),
            25.01..=50.0 => "medium".to_string(),
            50.01..=75.0 => "high".to_string(),
            75.01..=100.0 => "critical".to_string(),
            _ => "unknown".to_string(),
        }
    }

    /// Trend analysis (simplified)
    pub fn calculate_trend(&self, current_score: f64, previous_score: f64) -> String {
        let diff = current_score - previous_score;
        if diff > 5.0 {
            "improving".to_string()
        } else if diff < -5.0 {
            "degrading".to_string()
        } else {
            "stable".to_string()
        }
    }
}

impl Default for Scorer {
    fn default() -> Self {
        Self::new()
    }
}

/// Risk scorecard for a resource
pub struct RiskScorecard {
    pub resource_id: String,
    pub resource_type: String,
    pub timestamp: String,
    pub reliability_score: f64,
    pub performance_score: f64,
    pub maintainability_score: f64,
    pub security_score: f64,
    pub cost_efficiency_score: f64,
    pub overall_health_score: f64,
    pub risk_level: String,
}

impl RiskScorecard {
    pub fn new(resource_id: String, resource_type: String) -> Self {
        let scorer = Scorer::new();
        let overall = scorer.calculate_health_score(75.0, 75.0, 75.0);

        RiskScorecard {
            resource_id,
            resource_type,
            timestamp: chrono::Local::now().to_rfc3339(),
            reliability_score: 75.0,
            performance_score: 75.0,
            maintainability_score: 75.0,
            security_score: 75.0,
            cost_efficiency_score: 75.0,
            overall_health_score: overall,
            risk_level: scorer.categorize_risk(overall),
        }
    }

    pub fn to_dict(&self) -> HashMap<String, String> {
        vec![
            ("resource_id".to_string(), self.resource_id.clone()),
            ("resource_type".to_string(), self.resource_type.clone()),
            ("timestamp".to_string(), self.timestamp.clone()),
            ("reliability_score".to_string(), self.reliability_score.to_string()),
            ("performance_score".to_string(), self.performance_score.to_string()),
            ("maintainability_score".to_string(), self.maintainability_score.to_string()),
            ("security_score".to_string(), self.security_score.to_string()),
            ("cost_efficiency_score".to_string(), self.cost_efficiency_score.to_string()),
            ("overall_health_score".to_string(), self.overall_health_score.to_string()),
            ("risk_level".to_string(), self.risk_level.clone()),
        ]
        .into_iter()
        .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_violation(severity: &str) -> RuleViolation {
        RuleViolation::new(
            "TEST001".to_string(),
            Severity::Medium,
            "test_resource".to_string(),
            "Test violation".to_string(),
            "Fix test".to_string(),
        )
    }

    #[test]
    fn test_risk_score_calculation_no_violations() {
        let scorer = Scorer::new();
        let violations = vec![];
        let score = scorer.calculate_risk_score(&violations);
        assert_eq!(score, 100.0);
    }

    #[test]
    fn test_aggregate_by_severity() {
        let scorer = Scorer::new();
        let violations = vec![
            create_test_violation("high"),
            create_test_violation("medium"),
            create_test_violation("low"),
        ];

        let aggregated = scorer.aggregate_by_severity(&violations);
        assert_eq!(aggregated.get("medium").unwrap_or(&0), &1);
    }

    #[test]
    fn test_categorize_risk() {
        let scorer = Scorer::new();
        assert_eq!(scorer.categorize_risk(10.0), "low");
        assert_eq!(scorer.categorize_risk(40.0), "medium");
        assert_eq!(scorer.categorize_risk(60.0), "high");
        assert_eq!(scorer.categorize_risk(85.0), "critical");
    }

    #[test]
    fn test_calculate_health_score() {
        let scorer = Scorer::new();
        let health = scorer.calculate_health_score(100.0, 100.0, 100.0);
        assert_eq!(health, 100.0);

        let health = scorer.calculate_health_score(0.0, 0.0, 0.0);
        assert_eq!(health, 0.0);
    }

    #[test]
    fn test_calculate_trend() {
        let scorer = Scorer::new();
        assert_eq!(scorer.calculate_trend(80.0, 70.0), "improving");
        assert_eq!(scorer.calculate_trend(70.0, 80.0), "degrading");
        assert_eq!(scorer.calculate_trend(75.0, 75.0), "stable");
    }

    #[test]
    fn test_risk_scorecard() {
        let scorecard = RiskScorecard::new("dag_1".to_string(), "dag".to_string());
        assert_eq!(scorecard.resource_id, "dag_1");
        assert_eq!(scorecard.resource_type, "dag");
    }
}
