use std::fs;
use std::path::{Path, PathBuf};
use regex::Regex;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum DagParseError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Invalid Python syntax: {0}")]
    SyntaxError(String),

    #[error("Parse error: {0}")]
    ParseError(String),
}

/// Represents a parsed Airflow DAG
#[derive(Debug, Clone)]
pub struct DagDefinition {
    pub dag_id: String,
    pub file_path: String,
    pub source_code: String,
    pub parse_time_ms: f64,
    pub task_count: usize,
    pub task_ids: Vec<String>,
    pub max_task_depth: usize,
    pub has_cycles: bool,
    pub dynamic_dag_detected: bool,
    pub expensive_imports: Vec<String>,
    pub external_dependencies: Vec<String>,
}

impl DagDefinition {
    pub fn new(dag_id: String, file_path: String, source_code: String) -> Self {
        DagDefinition {
            dag_id,
            file_path,
            source_code,
            parse_time_ms: 0.0,
            task_count: 0,
            task_ids: Vec::new(),
            max_task_depth: 0,
            has_cycles: false,
            dynamic_dag_detected: false,
            expensive_imports: Vec::new(),
            external_dependencies: Vec::new(),
        }
    }
}

/// DAG Parser
pub struct DagParser {
    expensive_imports: Vec<String>,
}

impl DagParser {
    pub fn new() -> Self {
        DagParser {
            expensive_imports: vec![
                "tensorflow".to_string(),
                "torch".to_string(),
                "sklearn".to_string(),
                "pandas".to_string(),
                "numpy".to_string(),
            ],
        }
    }

    /// Parse a single DAG file
    pub fn parse_file(&self, file_path: &Path) -> Result<DagDefinition, DagParseError> {
        let source_code = fs::read_to_string(file_path)?;
        let dag_id = self.extract_dag_id(&source_code)
            .unwrap_or_else(|| {
                file_path
                    .file_stem()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown")
                    .to_string()
            });

        let mut dag = DagDefinition::new(
            dag_id,
            file_path.to_string_lossy().to_string(),
            source_code,
        );

        // Extract metadata
        dag.task_count = self.count_tasks(&dag.source_code);
        dag.task_ids = self.extract_task_ids(&dag.source_code);
        dag.max_task_depth = self.calculate_max_depth(&dag.task_ids);
        dag.has_cycles = self.detect_cycles(&dag.source_code);
        dag.dynamic_dag_detected = self.detect_dynamic_dag(&dag.source_code);
        dag.expensive_imports = self.detect_expensive_imports(&dag.source_code);
        dag.external_dependencies = self.detect_external_dependencies(&dag.source_code);

        Ok(dag)
    }

    /// Parse all DAG files in a directory
    pub fn parse_directory(&self, dir_path: &Path) -> Result<Vec<DagDefinition>, DagParseError> {
        let mut dags = Vec::new();

        for entry in fs::read_dir(dir_path)? {
            let entry = entry?;
            let path = entry.path();

            if path.is_file() && path.extension().map_or(false, |ext| ext == "py") {
                if let Ok(dag) = self.parse_file(&path) {
                    dags.push(dag);
                }
            }
        }

        Ok(dags)
    }

    /// Extract DAG ID from source code
    fn extract_dag_id(&self, source: &str) -> Option<String> {
        let re = Regex::new(r#"dag_id\s*=\s*["\']([^"\']+)["\']\s*[,)]"#).ok()?;
        re.captures(source)
            .and_then(|cap| cap.get(1))
            .map(|m| m.as_str().to_string())
    }

    /// Count task definitions
    fn count_tasks(&self, source: &str) -> usize {
        let patterns = [
            r"@dag\(\s*dag_id",
            r"DAG\s*\(",
            r"@task\(",
            r"@task_group\(",
            r"PythonOperator\(",
            r"BashOperator\(",
            r"SqlOperator\(",
            r"KubernetesPodOperator\(",
        ];

        let mut count = 0;
        for pattern in &patterns {
            if let Ok(re) = Regex::new(pattern) {
                count += re.find_iter(source).count();
            }
        }
        count
    }

    /// Extract task IDs
    fn extract_task_ids(&self, source: &str) -> Vec<String> {
        let mut ids = Vec::new();
        let re = Regex::new(r#"task_id\s*=\s*["\']([^"\']+)["\']\s*[,)]"#)
            .unwrap_or_else(|_| Regex::new("$^").unwrap()); // Never matches

        for cap in re.captures_iter(source) {
            if let Some(m) = cap.get(1) {
                ids.push(m.as_str().to_string());
            }
        }
        ids
    }

    /// Calculate maximum task dependency depth
    fn calculate_max_depth(&self, _task_ids: &[String]) -> usize {
        // Simplified: would need actual dependency analysis
        // For now, return a default depth
        5
    }

    /// Detect circular dependencies
    fn detect_cycles(&self, source: &str) -> bool {
        // Simple heuristic: look for patterns that might indicate cycles
        let cycle_patterns = [
            r"\s*>>\s*.*>>\s*.*>>\s*\1", // self-reference
            r"\.set_upstream\(.*\.set_upstream", // chained upstream
        ];

        for pattern in &cycle_patterns {
            if let Ok(re) = Regex::new(pattern) {
                if re.is_match(source) {
                    return true;
                }
            }
        }
        false
    }

    /// Detect dynamic DAG patterns
    fn detect_dynamic_dag(&self, source: &str) -> bool {
        let dynamic_patterns = [
            r"for\s+\w+\s+in\s+.*:",
            r"while\s+.*:",
            r"globals\(\)",
            r"@task_group\(",
            r"expand\(",
        ];

        for pattern in &dynamic_patterns {
            if let Ok(re) = Regex::new(pattern) {
                if re.is_match(source) {
                    return true;
                }
            }
        }
        false
    }

    /// Detect expensive imports
    fn detect_expensive_imports(&self, source: &str) -> Vec<String> {
        let mut imports = Vec::new();

        for expensive in &self.expensive_imports {
            let pattern = format!(r"import\s+{}|from\s+{}\s+import", expensive, expensive);
            if let Ok(re) = Regex::new(&pattern) {
                if re.is_match(source) {
                    imports.push(expensive.clone());
                }
            }
        }

        imports
    }

    /// Detect external service dependencies
    fn detect_external_dependencies(&self, source: &str) -> Vec<String> {
        let mut deps = Vec::new();

        let patterns = vec![
            ("S3", r"s3://|s3\..*|S3.*Operator"),
            ("BigQuery", r"BigQuery.*|bigquery\.|BQ.*"),
            ("Snowflake", r"Snowflake.*|SnowflakeOperator"),
            ("PostgreSQL", r"Postgres.*|psycopg"),
            ("MySQL", r"Mysql.*|mysql"),
            ("Redshift", r"Redshift.*|redshift"),
            ("API", r"requests\.|http\."),
        ];

        for (name, pattern) in patterns {
            if let Ok(re) = Regex::new(pattern) {
                if re.is_match(source) {
                    deps.push(name.to_string());
                }
            }
        }

        deps
    }
}

impl Default for DagParser {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn test_extract_dag_id() {
        let parser = DagParser::new();
        let source = r#"
from airflow import DAG
dag = DAG(
    dag_id="test_dag",
    default_args={}
)
"#;
        let dag_id = parser.extract_dag_id(source);
        assert_eq!(dag_id, Some("test_dag".to_string()));
    }

    #[test]
    fn test_detect_expensive_imports() {
        let parser = DagParser::new();
        let source = "import tensorflow as tf\nimport pandas as pd";
        let imports = parser.detect_expensive_imports(source);
        assert!(imports.contains(&"tensorflow".to_string()));
        assert!(imports.contains(&"pandas".to_string()));
    }

    #[test]
    fn test_detect_dynamic_dag() {
        let parser = DagParser::new();
        let source = "for i in range(10):\n    create_task()";
        assert!(parser.detect_dynamic_dag(source));
    }

    #[test]
    fn test_parse_file() {
        let parser = DagParser::new();
        let mut file = NamedTempFile::new().unwrap();
        writeln!(file, "dag_id = 'test_dag'\nprint('hello')").unwrap();

        let dag = parser.parse_file(file.path()).unwrap();
        assert_eq!(dag.dag_id, "test_dag");
    }
}
