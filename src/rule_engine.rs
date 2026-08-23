use std::collections::HashMap;

/// Context data for rule evaluation
pub struct RuleContext {
    pub dag_id: Option<String>,
    pub task_id: Option<String>,
    pub model_name: Option<String>,
    pub test_id: Option<String>,
    pub metadata: HashMap<String, String>,
}

impl Default for RuleContext {
    fn default() -> Self {
        Self::new()
    }
}

impl RuleContext {
    pub fn new() -> Self {
        RuleContext {
            dag_id: None,
            task_id: None,
            model_name: None,
            test_id: None,
            metadata: HashMap::new(),
        }
    }

    pub fn with_dag(mut self, dag_id: String) -> Self {
        self.dag_id = Some(dag_id);
        self
    }

    pub fn with_metadata(mut self, key: String, value: String) -> Self {
        self.metadata.insert(key, value);
        self
    }
}

/// Rule severity levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Severity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

impl Severity {
    pub fn as_str(&self) -> &'static str {
        match self {
            Severity::Critical => "critical",
            Severity::High => "high",
            Severity::Medium => "medium",
            Severity::Low => "low",
            Severity::Info => "info",
        }
    }

    pub fn from_str_name(s: &str) -> Option<Self> {
        match s {
            "critical" => Some(Severity::Critical),
            "high" => Some(Severity::High),
            "medium" => Some(Severity::Medium),
            "low" => Some(Severity::Low),
            "info" => Some(Severity::Info),
            _ => None,
        }
    }

    pub fn as_score(&self) -> u8 {
        match self {
            Severity::Critical => 100,
            Severity::High => 75,
            Severity::Medium => 50,
            Severity::Low => 25,
            Severity::Info => 10,
        }
    }
}

/// Rule category
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Category {
    Reliability,
    Performance,
    Maintainability,
    Security,
    Cost,
    DataQuality,
    Operational,
}

impl Category {
    pub fn as_str(&self) -> &'static str {
        match self {
            Category::Reliability => "reliability",
            Category::Performance => "performance",
            Category::Maintainability => "maintainability",
            Category::Security => "security",
            Category::Cost => "cost",
            Category::DataQuality => "data_quality",
            Category::Operational => "operational",
        }
    }
}

/// Execution mode for rules
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ExecutionMode {
    Static,
    Runtime,
    Correlation,
}

impl ExecutionMode {
    pub fn as_str(&self) -> &'static str {
        match self {
            ExecutionMode::Static => "static",
            ExecutionMode::Runtime => "runtime",
            ExecutionMode::Correlation => "correlation",
        }
    }
}

/// Base Rule trait
pub trait Rule: Send + Sync {
    fn id(&self) -> &str;
    fn name(&self) -> &str;
    fn severity(&self) -> Severity;
    fn category(&self) -> Category;
    fn execution_mode(&self) -> ExecutionMode;
    fn description(&self) -> &str;
    fn remediation(&self) -> &str;
    fn evaluate(&self, context: &RuleContext) -> Vec<RuleViolation>;
}

/// Rule violation result
#[derive(Debug, Clone)]
pub struct RuleViolation {
    pub rule_id: String,
    pub severity: Severity,
    pub affected_resource: String,
    pub message: String,
    pub remediation: String,
    pub context: HashMap<String, String>,
}

impl RuleViolation {
    pub fn new(
        rule_id: String,
        severity: Severity,
        affected_resource: String,
        message: String,
        remediation: String,
    ) -> Self {
        RuleViolation {
            rule_id,
            severity,
            affected_resource,
            message,
            remediation,
            context: HashMap::new(),
        }
    }

    pub fn with_context(mut self, key: String, value: String) -> Self {
        self.context.insert(key, value);
        self
    }
}

/// Rule engine for evaluating rules
pub struct RuleEngine {
    rules: Vec<Box<dyn Rule>>,
}

impl RuleEngine {
    pub fn new() -> Self {
        RuleEngine {
            rules: Vec::new(),
        }
    }

    pub fn register_rule(&mut self, rule: Box<dyn Rule>) {
        self.rules.push(rule);
    }

    pub fn evaluate(&self, context: &RuleContext) -> Vec<RuleViolation> {
        let mut violations = Vec::new();
        for rule in &self.rules {
            violations.extend(rule.evaluate(context));
        }
        violations
    }

    pub fn evaluate_by_mode(&self, context: &RuleContext, mode: ExecutionMode) -> Vec<RuleViolation> {
        let mut violations = Vec::new();
        for rule in &self.rules {
            if rule.execution_mode() == mode {
                violations.extend(rule.evaluate(context));
            }
        }
        violations
    }

    pub fn rule_count(&self) -> usize {
        self.rules.len()
    }
}

impl Default for RuleEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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
    fn test_severity_scoring() {
        assert_eq!(Severity::Critical.as_score(), 100);
        assert_eq!(Severity::High.as_score(), 75);
        assert_eq!(Severity::Medium.as_score(), 50);
        assert_eq!(Severity::Low.as_score(), 25);
        assert_eq!(Severity::Info.as_score(), 10);
    }

    #[test]
    fn test_rule_engine() {
        let mut engine = RuleEngine::new();
        engine.register_rule(Box::new(TestRule));
        assert_eq!(engine.rule_count(), 1);

        let context = RuleContext::new();
        let violations = engine.evaluate(&context);
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
}
