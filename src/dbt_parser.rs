use serde_json::Value;
use std::fs;
use std::path::Path;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum DbtParseError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("JSON parse error: {0}")]
    JsonError(#[from] serde_json::Error),

    #[error("Parse error: {0}")]
    ParseError(String),
}

/// Represents a parsed dbt model
#[derive(Debug, Clone)]
pub struct DbtModel {
    pub name: String,
    pub materialization: String,
    pub description: String,
    pub columns: Vec<String>,
    pub tests: Vec<String>,
    pub downstream_models: Vec<String>,
    pub upstream_models: Vec<String>,
    pub source_file: String,
}

impl DbtModel {
    pub fn new(name: String) -> Self {
        DbtModel {
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
}

/// Represents a parsed dbt test
#[derive(Debug, Clone)]
pub struct DbtTest {
    pub name: String,
    pub test_type: String,
    pub model_name: String,
    pub source_name: Option<String>,
    pub column_name: Option<String>,
    pub properties: std::collections::HashMap<String, String>,
}

impl DbtTest {
    pub fn new(name: String, test_type: String, model_name: String) -> Self {
        DbtTest {
            name,
            test_type,
            model_name,
            source_name: None,
            column_name: None,
            properties: std::collections::HashMap::new(),
        }
    }
}

/// Represents a parsed dbt project
#[derive(Debug, Clone)]
pub struct DbtProject {
    pub name: String,
    pub models: Vec<DbtModel>,
    pub tests: Vec<DbtTest>,
    pub sources: Vec<String>,
    pub lineage_graph: std::collections::HashMap<String, Vec<String>>,
}

impl DbtProject {
    pub fn new(name: String) -> Self {
        DbtProject {
            name,
            models: Vec::new(),
            tests: Vec::new(),
            sources: Vec::new(),
            lineage_graph: std::collections::HashMap::new(),
        }
    }
}

/// dbt project parser
pub struct DbtParser;

impl DbtParser {
    /// Parse dbt manifest.json
    pub fn parse_manifest(manifest_path: &Path) -> Result<DbtProject, DbtParseError> {
        let content = fs::read_to_string(manifest_path)?;
        let manifest: Value = serde_json::from_str(&content)?;

        let mut project = DbtProject::new(
            manifest
                .get("metadata")
                .and_then(|m| m.get("dbt_schema_version"))
                .and_then(|v| v.as_str())
                .unwrap_or("unknown")
                .to_string(),
        );

        // Parse models
        if let Some(nodes) = manifest.get("nodes").and_then(|n| n.as_object()) {
            for (key, node) in nodes {
                if key.starts_with("model.") {
                    if let Ok(model) = DbtParser::parse_model_node(node) {
                        project.models.push(model);
                    }
                }
            }
        }

        // Parse tests
        if let Some(nodes) = manifest.get("nodes").and_then(|n| n.as_object()) {
            for (key, node) in nodes {
                if key.starts_with("test.") {
                    if let Ok(test) = DbtParser::parse_test_node(node) {
                        project.tests.push(test);
                    }
                }
            }
        }

        // Build lineage graph
        project.lineage_graph = DbtParser::build_lineage_graph(&manifest)?;

        Ok(project)
    }

    /// Parse a single model node from manifest
    fn parse_model_node(node: &Value) -> Result<DbtModel, DbtParseError> {
        let name = node
            .get("name")
            .and_then(|n| n.as_str())
            .unwrap_or("unknown")
            .to_string();

        let mut model = DbtModel::new(name);

        model.materialization = node
            .get("config")
            .and_then(|c| c.get("materialized"))
            .and_then(|m| m.as_str())
            .unwrap_or("table")
            .to_string();

        model.description = node
            .get("description")
            .and_then(|d| d.as_str())
            .unwrap_or("")
            .to_string();

        model.source_file = node
            .get("path")
            .and_then(|p| p.as_str())
            .unwrap_or("")
            .to_string();

        // Extract column names
        if let Some(columns) = node.get("columns").and_then(|c| c.as_object()) {
            for col_name in columns.keys() {
                model.columns.push(col_name.clone());
            }
        }

        // Extract depends_on (upstream models)
        if let Some(depends_on) = node.get("depends_on").and_then(|d| d.get("nodes")) {
            if let Some(deps) = depends_on.as_array() {
                for dep in deps {
                    if let Some(dep_str) = dep.as_str() {
                        if dep_str.starts_with("model.") {
                            model.upstream_models.push(dep_str.to_string());
                        }
                    }
                }
            }
        }

        Ok(model)
    }

    /// Parse a single test node from manifest
    fn parse_test_node(node: &Value) -> Result<DbtTest, DbtParseError> {
        let name = node
            .get("name")
            .and_then(|n| n.as_str())
            .unwrap_or("unknown")
            .to_string();

        let test_type = node
            .get("test_metadata")
            .and_then(|t| t.get("name"))
            .and_then(|n| n.as_str())
            .unwrap_or("generic")
            .to_string();

        // Determine model name from attached_node or first depend_on
        let model_name = if let Some(attached) = node.get("attached_node").and_then(|a| a.as_str()) {
            attached.split('.').next_back().unwrap_or("unknown").to_string()
        } else if let Some(depends_on) = node
            .get("depends_on")
            .and_then(|d| d.get("nodes"))
            .and_then(|n| n.as_array())
            .and_then(|a| a.first())
            .and_then(|f| f.as_str())
        {
            depends_on.split('.').next_back().unwrap_or("unknown").to_string()
        } else {
            "unknown".to_string()
        };

        let mut test = DbtTest::new(name, test_type, model_name);

        // Extract column name if present
        if let Some(args) = node.get("test_metadata").and_then(|t| t.get("kwargs")) {
            if let Some(col) = args.get("column_name").and_then(|c| c.as_str()) {
                test.column_name = Some(col.to_string());
            }
        }

        Ok(test)
    }

    /// Build lineage graph from manifest
    fn build_lineage_graph(
        manifest: &Value,
    ) -> Result<std::collections::HashMap<String, Vec<String>>, DbtParseError> {
        let mut graph = std::collections::HashMap::new();

        if let Some(nodes) = manifest.get("nodes").and_then(|n| n.as_object()) {
            for (key, node) in nodes {
                if key.starts_with("model.") {
                    if let Some(name) = node.get("name").and_then(|n| n.as_str()) {
                        let mut downstream = Vec::new();

                        // Find nodes that depend on this one
                        for (other_key, other_node) in nodes {
                            if other_key != key {
                                if let Some(depends_on) =
                                    other_node.get("depends_on").and_then(|d| d.get("nodes"))
                                {
                                    if let Some(deps) = depends_on.as_array() {
                                        for dep in deps {
                                            if let Some(dep_str) = dep.as_str() {
                                                if dep_str.contains(name) {
                                                    if let Some(other_name) =
                                                        other_node.get("name").and_then(|n| n.as_str())
                                                    {
                                                        downstream.push(other_name.to_string());
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        graph.insert(name.to_string(), downstream);
                    }
                }
            }
        }

        Ok(graph)
    }

    /// Parse dbt catalog.json for schema information
    pub fn parse_catalog(catalog_path: &Path) -> Result<std::collections::HashMap<String, Value>, DbtParseError> {
        let content = fs::read_to_string(catalog_path)?;
        let catalog: Value = serde_json::from_str(&content)?;

        let mut schemas = std::collections::HashMap::new();
        if let Some(sources) = catalog.get("sources").and_then(|s| s.as_object()) {
            for (key, source) in sources {
                schemas.insert(key.clone(), source.clone());
            }
        }

        Ok(schemas)
    }

    /// Parse dbt run_results.json for test execution results
    pub fn parse_run_results(
        run_results_path: &Path,
    ) -> Result<Vec<std::collections::HashMap<String, String>>, DbtParseError> {
        let content = fs::read_to_string(run_results_path)?;
        let results: Value = serde_json::from_str(&content)?;

        let mut test_results = Vec::new();
        if let Some(results_array) = results.get("results").and_then(|r| r.as_array()) {
            for result in results_array {
                let mut test_result = std::collections::HashMap::new();
                if let Some(name) = result.get("name").and_then(|n| n.as_str()) {
                    test_result.insert("name".to_string(), name.to_string());
                }
                if let Some(status) = result.get("status").and_then(|s| s.as_str()) {
                    test_result.insert("status".to_string(), status.to_string());
                }
                if let Some(execution_time) = result.get("execution_time").and_then(|e| e.as_f64()) {
                    test_result.insert("execution_time_ms".to_string(), (execution_time * 1000.0).to_string());
                }
                test_results.push(test_result);
            }
        }

        Ok(test_results)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_dbt_model() {
        let model = DbtModel::new("test_model".to_string());
        assert_eq!(model.name, "test_model");
        assert_eq!(model.materialization, "table");
    }

    #[test]
    fn test_create_dbt_test() {
        let test = DbtTest::new(
            "not_null_id".to_string(),
            "not_null".to_string(),
            "customers".to_string(),
        );
        assert_eq!(test.name, "not_null_id");
        assert_eq!(test.test_type, "not_null");
        assert_eq!(test.model_name, "customers");
    }

    #[test]
    fn test_create_dbt_project() {
        let mut project = DbtProject::new("my_project".to_string());
        project.models.push(DbtModel::new("model1".to_string()));
        assert_eq!(project.models.len(), 1);
    }
}
