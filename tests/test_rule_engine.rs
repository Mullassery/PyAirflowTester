use pyairflowtester::rule_engine::{RuleEngine, RuleContext, Rule, Severity, Category, ExecutionMode, RuleViolation};

struct TestRule;

impl Rule for TestRule {
    fn id(&self) -> &str {
        "TEST001"
    }

    fn name(&self) -> &str {
        "Test Rule"
    }

    fn severity(&self) -> Severity {
        Severity::Medium
    }

    fn category(&self) -> Category {
        Category::Reliability
    }

    fn execution_mode(&self) -> ExecutionMode {
        ExecutionMode::Static
    }

    fn description(&self) -> &str {
        "A test rule"
    }

    fn remediation(&self) -> &str {
        "No action needed"
    }

    fn evaluate(&self, _context: &RuleContext) -> Vec<RuleViolation> {
        vec![RuleViolation::new(
            self.id().to_string(),
            self.severity(),
            "test_resource".to_string(),
            "Test violation".to_string(),
            self.remediation().to_string(),
        )]
    }
}

#[test]
fn test_rule_engine_registration() {
    let mut engine = RuleEngine::new();
    engine.register_rule(Box::new(TestRule));
    assert_eq!(engine.rule_count(), 1);
}

#[test]
fn test_rule_evaluation() {
    let mut engine = RuleEngine::new();
    engine.register_rule(Box::new(TestRule));

    let context = RuleContext::new();
    let violations = engine.evaluate(&context);
    assert_eq!(violations.len(), 1);
    assert_eq!(violations[0].rule_id, "TEST001");
}

#[test]
fn test_rule_filtering_by_mode() {
    let mut engine = RuleEngine::new();
    engine.register_rule(Box::new(TestRule));

    let context = RuleContext::new();
    let violations = engine.evaluate_by_mode(&context, ExecutionMode::Static);
    assert_eq!(violations.len(), 1);
}

#[test]
fn test_context_building() {
    let context = RuleContext::new()
        .with_dag("test_dag".to_string())
        .with_metadata("key".to_string(), "value".to_string());

    assert_eq!(context.dag_id, Some("test_dag".to_string()));
    assert_eq!(context.metadata.get("key"), Some(&"value".to_string()));
}

#[test]
fn test_severity_scoring() {
    assert_eq!(Severity::Critical.as_score(), 100);
    assert_eq!(Severity::High.as_score(), 75);
    assert_eq!(Severity::Medium.as_score(), 50);
    assert_eq!(Severity::Low.as_score(), 25);
    assert_eq!(Severity::Info.as_score(), 10);
}

#[test]
fn test_severity_string_conversion() {
    assert_eq!(Severity::Critical.as_str(), "critical");
    assert_eq!(Severity::High.as_str(), "high");
    assert_eq!(Severity::from_str("critical"), Some(Severity::Critical));
    assert_eq!(Severity::from_str("invalid"), None);
}

#[test]
fn test_rule_violation_with_context() {
    let violation = RuleViolation::new(
        "TEST001".to_string(),
        Severity::High,
        "dag1".to_string(),
        "Test message".to_string(),
        "Test remediation".to_string(),
    )
    .with_context("key".to_string(), "value".to_string());

    assert_eq!(violation.context.get("key"), Some(&"value".to_string()));
}
