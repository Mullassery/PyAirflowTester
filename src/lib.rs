use pyo3::prelude::*;
use std::collections::HashMap;

pub mod rule_engine;
pub mod dag_parser;
pub mod dbt_parser;
pub mod scoring;

use rule_engine::{Rule, RuleViolation, RuleContext};

/// Python module for PyAirflowTester core functionality
#[pymodule]
fn _core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyRule>()?;
    m.add_class::<PyRuleViolation>()?;
    m.add_function(wrap_pyfunction!(evaluate_rules, m)?)?;
    Ok(())
}

/// Python wrapper for Rule
#[pyclass]
pub struct PyRule {
    pub id: String,
    pub name: String,
    pub severity: String,
    pub category: String,
    pub description: String,
}

#[pymethods]
impl PyRule {
    #[new]
    fn new(id: String, name: String, severity: String, category: String, description: String) -> Self {
        PyRule {
            id,
            name,
            severity,
            category,
            description,
        }
    }

    fn __repr__(&self) -> String {
        format!("Rule(id='{}', severity='{}')", self.id, self.severity)
    }
}

/// Python wrapper for RuleViolation
#[pyclass]
pub struct PyRuleViolation {
    pub rule_id: String,
    pub severity: String,
    pub affected_resource: String,
    pub message: String,
    pub remediation: String,
}

#[pymethods]
impl PyRuleViolation {
    #[new]
    fn new(
        rule_id: String,
        severity: String,
        affected_resource: String,
        message: String,
        remediation: String,
    ) -> Self {
        PyRuleViolation {
            rule_id,
            severity,
            affected_resource,
            message,
            remediation,
        }
    }

    fn __repr__(&self) -> String {
        format!("Violation(rule='{}', resource='{}')", self.rule_id, self.affected_resource)
    }

    fn to_dict(&self) -> HashMap<String, String> {
        vec![
            ("rule_id".to_string(), self.rule_id.clone()),
            ("severity".to_string(), self.severity.clone()),
            ("affected_resource".to_string(), self.affected_resource.clone()),
            ("message".to_string(), self.message.clone()),
            ("remediation".to_string(), self.remediation.clone()),
        ]
        .into_iter()
        .collect()
    }
}

/// Evaluate rules against context
#[pyfunction]
fn evaluate_rules(rule_ids: Vec<String>, context_data: HashMap<String, String>) -> PyResult<Vec<PyRuleViolation>> {
    let mut violations = Vec::new();

    for rule_id in rule_ids {
        let violation = PyRuleViolation {
            rule_id: rule_id.clone(),
            severity: "info".to_string(),
            affected_resource: "test".to_string(),
            message: format!("Rule {} evaluated", rule_id),
            remediation: "No action needed".to_string(),
        };
        violations.push(violation);
    }

    Ok(violations)
}
