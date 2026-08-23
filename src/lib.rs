// pyo3 0.20's #[pymethods] macro expands to an `impl` block that trips the
// `non_local_definitions` lint on newer (beta/future-stable) rustc -- the
// lint's own diagnostic says as much ("may come from an old version of the
// pyo3_macros crate"). It's generated code we don't control, not a real
// issue in this crate's own code; a pyo3 major-version bump would fix it
// properly but is a larger, separate migration. Suppress it here.
#![allow(non_local_definitions)]

use pyo3::prelude::*;
use std::collections::HashMap;
use std::path::Path;

pub mod rule_engine;
pub mod dag_parser;
pub mod dbt_parser;
pub mod scoring;

use rule_engine::{RuleViolation, Severity, RuleEngine};
use dag_parser::{DagParser, DagDefinition};
use dbt_parser::{DbtParser, DbtProject, DbtModel, DbtTest};
use scoring::Scorer;

/// Python module for PyAirflowTester core functionality
#[pymodule]
fn _core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyRule>()?;
    m.add_class::<PyRuleViolation>()?;
    m.add_class::<PySeverity>()?;
    m.add_class::<PyCategory>()?;
    m.add_class::<PyExecutionMode>()?;
    m.add_class::<PyRuleContext>()?;
    m.add_class::<PyRuleEngine>()?;
    m.add_class::<PyDagDefinition>()?;
    m.add_class::<PyDagParser>()?;
    m.add_class::<PyDbtModel>()?;
    m.add_class::<PyDbtTest>()?;
    m.add_class::<PyDbtProject>()?;
    m.add_class::<PyDbtParser>()?;
    m.add_class::<PyScorer>()?;
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

// ============================================================================
// SEVERITY ENUM
// ============================================================================

#[pyclass]
#[derive(Clone)]
pub enum PySeverity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

#[pymethods]
impl PySeverity {
    #[staticmethod]
    fn critical() -> Self {
        PySeverity::Critical
    }

    #[staticmethod]
    fn high() -> Self {
        PySeverity::High
    }

    #[staticmethod]
    fn medium() -> Self {
        PySeverity::Medium
    }

    #[staticmethod]
    fn low() -> Self {
        PySeverity::Low
    }

    #[staticmethod]
    fn info() -> Self {
        PySeverity::Info
    }

    fn as_str(&self) -> String {
        match self {
            PySeverity::Critical => "critical".to_string(),
            PySeverity::High => "high".to_string(),
            PySeverity::Medium => "medium".to_string(),
            PySeverity::Low => "low".to_string(),
            PySeverity::Info => "info".to_string(),
        }
    }

    fn as_score(&self) -> u8 {
        match self {
            PySeverity::Critical => 100,
            PySeverity::High => 75,
            PySeverity::Medium => 50,
            PySeverity::Low => 25,
            PySeverity::Info => 10,
        }
    }
}

// ============================================================================
// CATEGORY ENUM
// ============================================================================

#[pyclass]
#[derive(Clone)]
pub enum PyCategory {
    Reliability,
    Performance,
    Maintainability,
    Security,
    Cost,
    DataQuality,
    Operational,
}

#[pymethods]
impl PyCategory {
    #[staticmethod]
    fn reliability() -> Self {
        PyCategory::Reliability
    }

    #[staticmethod]
    fn performance() -> Self {
        PyCategory::Performance
    }

    #[staticmethod]
    fn maintainability() -> Self {
        PyCategory::Maintainability
    }

    #[staticmethod]
    fn security() -> Self {
        PyCategory::Security
    }

    #[staticmethod]
    fn cost() -> Self {
        PyCategory::Cost
    }

    #[staticmethod]
    fn data_quality() -> Self {
        PyCategory::DataQuality
    }

    #[staticmethod]
    fn operational() -> Self {
        PyCategory::Operational
    }

    fn as_str(&self) -> String {
        match self {
            PyCategory::Reliability => "reliability".to_string(),
            PyCategory::Performance => "performance".to_string(),
            PyCategory::Maintainability => "maintainability".to_string(),
            PyCategory::Security => "security".to_string(),
            PyCategory::Cost => "cost".to_string(),
            PyCategory::DataQuality => "data_quality".to_string(),
            PyCategory::Operational => "operational".to_string(),
        }
    }
}

// ============================================================================
// EXECUTION MODE ENUM
// ============================================================================

#[pyclass]
#[derive(Clone)]
pub enum PyExecutionMode {
    Static,
    Runtime,
    Correlation,
}

#[pymethods]
impl PyExecutionMode {
    #[staticmethod]
    fn static_mode() -> Self {
        PyExecutionMode::Static
    }

    #[staticmethod]
    fn runtime() -> Self {
        PyExecutionMode::Runtime
    }

    #[staticmethod]
    fn correlation() -> Self {
        PyExecutionMode::Correlation
    }

    fn as_str(&self) -> String {
        match self {
            PyExecutionMode::Static => "static".to_string(),
            PyExecutionMode::Runtime => "runtime".to_string(),
            PyExecutionMode::Correlation => "correlation".to_string(),
        }
    }
}

// ============================================================================
// RULE CONTEXT CLASS
// ============================================================================

#[pyclass]
pub struct PyRuleContext {
    dag_id: Option<String>,
    task_id: Option<String>,
    model_name: Option<String>,
    test_id: Option<String>,
    metadata: HashMap<String, String>,
}

#[pymethods]
impl PyRuleContext {
    #[new]
    fn new() -> Self {
        PyRuleContext {
            dag_id: None,
            task_id: None,
            model_name: None,
            test_id: None,
            metadata: HashMap::new(),
        }
    }

    fn with_dag(&mut self, dag_id: String) -> PyResult<PyObject> {
        self.dag_id = Some(dag_id);
        Ok(Python::with_gil(|py| py.None()))
    }

    fn with_task(&mut self, task_id: String) -> PyResult<PyObject> {
        self.task_id = Some(task_id);
        Ok(Python::with_gil(|py| py.None()))
    }

    fn with_model(&mut self, model_name: String) -> PyResult<PyObject> {
        self.model_name = Some(model_name);
        Ok(Python::with_gil(|py| py.None()))
    }

    fn with_test(&mut self, test_id: String) -> PyResult<PyObject> {
        self.test_id = Some(test_id);
        Ok(Python::with_gil(|py| py.None()))
    }

    fn with_metadata(&mut self, key: String, value: String) -> PyResult<PyObject> {
        self.metadata.insert(key, value);
        Ok(Python::with_gil(|py| py.None()))
    }

    #[getter]
    fn dag_id(&self) -> Option<String> {
        self.dag_id.clone()
    }

    #[getter]
    fn task_id(&self) -> Option<String> {
        self.task_id.clone()
    }

    #[getter]
    fn model_name(&self) -> Option<String> {
        self.model_name.clone()
    }

    #[getter]
    fn test_id(&self) -> Option<String> {
        self.test_id.clone()
    }

    #[getter]
    fn metadata(&self) -> HashMap<String, String> {
        self.metadata.clone()
    }

    fn __repr__(&self) -> String {
        format!("RuleContext(dag={:?}, task={:?})", self.dag_id, self.task_id)
    }
}

// ============================================================================
// RULE ENGINE CLASS
// ============================================================================

#[pyclass]
pub struct PyRuleEngine {
    inner: RuleEngine,
}

#[pymethods]
impl PyRuleEngine {
    #[new]
    fn new() -> Self {
        PyRuleEngine {
            inner: RuleEngine::new(),
        }
    }

    fn rule_count(&self) -> usize {
        self.inner.rule_count()
    }

    fn __repr__(&self) -> String {
        format!("RuleEngine(rules={})", self.inner.rule_count())
    }
}

// ============================================================================
// DAG DEFINITION CLASS
// ============================================================================

#[pyclass]
pub struct PyDagDefinition {
    #[pyo3(get)]
    pub dag_id: String,
    #[pyo3(get)]
    pub file_path: String,
    #[pyo3(get)]
    pub task_count: usize,
    #[pyo3(get)]
    pub task_ids: Vec<String>,
    #[pyo3(get)]
    pub max_task_depth: usize,
    #[pyo3(get)]
    pub has_cycles: bool,
    #[pyo3(get)]
    pub dynamic_dag_detected: bool,
    #[pyo3(get)]
    pub expensive_imports: Vec<String>,
    #[pyo3(get)]
    pub external_dependencies: Vec<String>,
}

#[pymethods]
impl PyDagDefinition {
    fn __repr__(&self) -> String {
        format!("DagDefinition(dag_id='{}', tasks={})", self.dag_id, self.task_count)
    }
}

fn convert_dag_definition(dag: DagDefinition) -> PyDagDefinition {
    PyDagDefinition {
        dag_id: dag.dag_id,
        file_path: dag.file_path,
        task_count: dag.task_count,
        task_ids: dag.task_ids,
        max_task_depth: dag.max_task_depth,
        has_cycles: dag.has_cycles,
        dynamic_dag_detected: dag.dynamic_dag_detected,
        expensive_imports: dag.expensive_imports,
        external_dependencies: dag.external_dependencies,
    }
}

// ============================================================================
// DAG PARSER CLASS
// ============================================================================

#[pyclass]
pub struct PyDagParser {
    inner: DagParser,
}

#[pymethods]
impl PyDagParser {
    #[new]
    fn new() -> Self {
        PyDagParser {
            inner: DagParser::new(),
        }
    }

    fn parse_file(&self, file_path: &str) -> PyResult<PyDagDefinition> {
        self.inner
            .parse_file(Path::new(file_path))
            .map(convert_dag_definition)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    fn parse_directory(&self, dir_path: &str) -> PyResult<Vec<PyDagDefinition>> {
        self.inner
            .parse_directory(Path::new(dir_path))
            .map(|dags| dags.into_iter().map(convert_dag_definition).collect())
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    fn __repr__(&self) -> String {
        "DagParser()".to_string()
    }
}

// ============================================================================
// DBT MODEL CLASS
// ============================================================================

#[pyclass]
#[derive(Clone)]
pub struct PyDbtModel {
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub materialization: String,
    #[pyo3(get, set)]
    pub description: String,
    #[pyo3(get, set)]
    pub columns: Vec<String>,
    #[pyo3(get, set)]
    pub tests: Vec<String>,
    #[pyo3(get, set)]
    pub downstream_models: Vec<String>,
    #[pyo3(get, set)]
    pub upstream_models: Vec<String>,
    #[pyo3(get)]
    pub source_file: String,
}

#[pymethods]
impl PyDbtModel {
    #[new]
    fn new(name: String) -> Self {
        PyDbtModel {
            name,
            materialization: "table".to_string(),
            description: String::new(),
            columns: Vec::new(),
            tests: Vec::new(),
            downstream_models: Vec::new(),
            upstream_models: Vec::new(),
            source_file: String::new(),
        }
    }

    fn __repr__(&self) -> String {
        format!("DbtModel(name='{}', materialization='{}')", self.name, self.materialization)
    }
}

fn convert_dbt_model(model: DbtModel) -> PyDbtModel {
    PyDbtModel {
        name: model.name,
        materialization: model.materialization,
        description: model.description,
        columns: model.columns,
        tests: model.tests,
        downstream_models: model.downstream_models,
        upstream_models: model.upstream_models,
        source_file: model.source_file,
    }
}

// ============================================================================
// DBT TEST CLASS
// ============================================================================

#[pyclass]
#[derive(Clone)]
pub struct PyDbtTest {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub test_type: String,
    #[pyo3(get)]
    pub model_name: String,
    #[pyo3(get)]
    pub source_name: Option<String>,
    #[pyo3(get)]
    pub column_name: Option<String>,
    #[pyo3(get)]
    pub properties: HashMap<String, String>,
}

#[pymethods]
impl PyDbtTest {
    fn __repr__(&self) -> String {
        format!("DbtTest(name='{}', type='{}')", self.name, self.test_type)
    }
}

fn convert_dbt_test(test: DbtTest) -> PyDbtTest {
    PyDbtTest {
        name: test.name,
        test_type: test.test_type,
        model_name: test.model_name,
        source_name: test.source_name,
        column_name: test.column_name,
        properties: test.properties,
    }
}

// ============================================================================
// DBT PROJECT CLASS
// ============================================================================

#[pyclass]
pub struct PyDbtProject {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub models: Vec<PyDbtModel>,
    #[pyo3(get)]
    pub tests: Vec<PyDbtTest>,
    #[pyo3(get)]
    pub sources: Vec<String>,
    #[pyo3(get)]
    pub lineage_graph: HashMap<String, Vec<String>>,
}

#[pymethods]
impl PyDbtProject {
    fn model_count(&self) -> usize {
        self.models.len()
    }

    fn test_count(&self) -> usize {
        self.tests.len()
    }

    fn __repr__(&self) -> String {
        format!("DbtProject(name='{}', models={}, tests={})", self.name, self.models.len(), self.tests.len())
    }
}

fn convert_dbt_project(project: DbtProject) -> PyDbtProject {
    PyDbtProject {
        name: project.name,
        models: project.models.into_iter().map(convert_dbt_model).collect(),
        tests: project.tests.into_iter().map(convert_dbt_test).collect(),
        sources: project.sources,
        lineage_graph: project.lineage_graph,
    }
}

// ============================================================================
// DBT PARSER CLASS
// ============================================================================

#[pyclass]
pub struct PyDbtParser;

#[pymethods]
impl PyDbtParser {
    #[new]
    fn new() -> Self {
        PyDbtParser
    }

    #[staticmethod]
    fn parse_manifest(manifest_path: &str) -> PyResult<PyDbtProject> {
        DbtParser::parse_manifest(Path::new(manifest_path))
            .map(convert_dbt_project)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    fn __repr__(&self) -> String {
        "DbtParser()".to_string()
    }
}

// ============================================================================
// SCORER CLASS
// ============================================================================

#[pyclass]
pub struct PyScorer {
    inner: Scorer,
}

#[pymethods]
impl PyScorer {
    #[new]
    fn new() -> Self {
        PyScorer {
            inner: Scorer::new(),
        }
    }

    fn calculate_priority_score(&self, rule_id: &str, severity_str: &str) -> PyResult<f64> {
        let severity = Severity::from_str_name(severity_str).unwrap_or(Severity::Info);
        let violation = RuleViolation::new(
            rule_id.to_string(),
            severity,
            "resource".to_string(),
            "message".to_string(),
            "remediation".to_string(),
        );
        Ok(self.inner.calculate_priority_score(&violation))
    }

    fn __repr__(&self) -> String {
        "Scorer()".to_string()
    }
}

/// Evaluate rules against context
#[pyfunction]
fn evaluate_rules(rule_ids: Vec<String>, _context_data: HashMap<String, String>) -> PyResult<Vec<PyRuleViolation>> {
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
