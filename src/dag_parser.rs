use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::Path;
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
        dag.max_task_depth = self.calculate_max_depth(&dag.source_code);
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

            if path.is_file() && path.extension().is_some_and(|ext| ext == "py") {
                if let Ok(dag) = self.parse_file(&path) {
                    dags.push(dag);
                }
            }
        }

        Ok(dags)
    }

    /// Extract DAG ID from source code
    fn extract_dag_id(&self, source: &str) -> Option<String> {
        // No longer requires a trailing `,`/`)` after the closing quote --
        // that made this only match `dag_id` used as a call keyword
        // argument (e.g. `DAG(dag_id="x", ...)`), not a plain assignment
        // statement (`dag_id = "x"`), which is equally valid Python and is
        // what a bare-string-literal closing quote followed by anything
        // else (newline, EOF, another statement) looks like.
        let re = Regex::new(r#"dag_id\s*=\s*["\']([^"\']+)["\']"#).ok()?;
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

    /// Calculate the maximum task dependency depth.
    ///
    /// Walks the real dependency graph built from the DAG source and returns
    /// the number of tasks in its longest dependency chain (a linear
    /// `a >> b >> c` has depth 3; a DAG whose tasks are all independent has
    /// depth 1; a DAG with no tasks has depth 0). Dependencies are read from
    /// `>>`/`<<` chains (including list operands such as `[a, b] >> c`) and
    /// from `task.set_upstream(...)` / `task.set_downstream(...)` calls.
    ///
    /// Previously this was a stub that ignored its input entirely and always
    /// returned a hardcoded `5` for every DAG.
    fn calculate_max_depth(&self, source: &str) -> usize {
        let (nodes, edges) = self.build_dependency_edges(source);
        if nodes.is_empty() {
            return 0;
        }

        // Longest path measured in nodes, memoized across the (necessarily
        // acyclic in valid DAGs) graph. The `on_stack` set guards against
        // cycles so malformed input can't cause unbounded recursion;
        // `detect_cycles` reports those separately.
        let mut memo: HashMap<String, usize> = HashMap::new();
        let mut on_stack: HashSet<String> = HashSet::new();
        let mut max_depth = 1;
        for node in &nodes {
            max_depth = max_depth.max(longest_chain(node, &edges, &mut memo, &mut on_stack));
        }
        max_depth
    }

    /// Build the dependency graph from DAG source.
    ///
    /// Returns the set of task nodes and an adjacency map of `from -> [to]`
    /// edges, read from `>>`/`<<` chains (including list operands such as
    /// `[a, b] >> c`) and from `task.set_upstream(...)` /
    /// `task.set_downstream(...)` calls. Local variable names are resolved to
    /// their declared `task_id` where possible.
    fn build_dependency_edges(
        &self,
        source: &str,
    ) -> (HashSet<String>, HashMap<String, Vec<String>>) {
        // Map local variable names to their declared `task_id` so edges
        // written in terms of variables (`extract >> transform`) can be
        // resolved to stable task ids. Falls back to the variable name when
        // no `task_id` is declared (e.g. `@task`-decorated callables).
        let var_to_task = extract_var_to_task_map(source);
        let resolve = |name: &str| -> String {
            let name = name.trim().trim_end_matches("()");
            var_to_task
                .get(name)
                .cloned()
                .unwrap_or_else(|| name.to_string())
        };
        let parse_side = |seg: &str| -> Vec<String> {
            seg.trim()
                .trim_start_matches('[')
                .trim_end_matches(']')
                .split(',')
                .map(&resolve)
                .filter(|s| !s.is_empty())
                .collect()
        };

        let mut nodes: HashSet<String> = self.extract_task_ids(source).into_iter().collect();
        let mut edges: HashMap<String, Vec<String>> = HashMap::new();
        let mut add_edge = |from: String, to: String| {
            if from.is_empty() || to.is_empty() {
                return;
            }
            nodes.insert(from.clone());
            nodes.insert(to.clone());
            edges.entry(from).or_default().push(to);
        };

        for raw_line in source.lines() {
            let line = raw_line.trim();
            if line.starts_with('#') {
                continue;
            }
            if line.contains(">>") {
                let segs: Vec<&str> = line.split(">>").collect();
                for w in segs.windows(2) {
                    for a in parse_side(w[0]) {
                        for b in parse_side(w[1]) {
                            add_edge(a.clone(), b.clone());
                        }
                    }
                }
            } else if line.contains("<<") {
                // `a << b` means b is upstream of a, i.e. edge b -> a.
                let segs: Vec<&str> = line.split("<<").collect();
                for w in segs.windows(2) {
                    for a in parse_side(w[1]) {
                        for b in parse_side(w[0]) {
                            add_edge(a.clone(), b.clone());
                        }
                    }
                }
            }
        }

        if let Ok(re) = Regex::new(r"(\w+)\.set_upstream\(([^)]*)\)") {
            for cap in re.captures_iter(source) {
                let downstream = resolve(&cap[1]);
                for upstream in parse_side(&cap[2]) {
                    add_edge(upstream, downstream.clone());
                }
            }
        }
        if let Ok(re) = Regex::new(r"(\w+)\.set_downstream\(([^)]*)\)") {
            for cap in re.captures_iter(source) {
                let upstream = resolve(&cap[1]);
                for downstream in parse_side(&cap[2]) {
                    add_edge(upstream.clone(), downstream);
                }
            }
        }

        (nodes, edges)
    }

    /// Detect circular dependencies using a depth-first search over the real
    /// dependency graph.
    ///
    /// The previous implementation was a regex "heuristic" whose primary
    /// pattern used a `\1` backreference (unsupported by the `regex` crate),
    /// so `Regex::new` always failed and the pattern was silently skipped,
    /// leaving only a loose `.set_upstream(...).set_upstream` substring match
    /// that never detected an actual cycle.
    fn detect_cycles(&self, source: &str) -> bool {
        let (nodes, edges) = self.build_dependency_edges(source);
        let mut visiting: HashSet<String> = HashSet::new();
        let mut visited: HashSet<String> = HashSet::new();
        for node in &nodes {
            if has_cycle_from(node, &edges, &mut visiting, &mut visited) {
                return true;
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

/// Build a map from assigned variable names to declared `task_id` values.
///
/// Matches the common Airflow idiom of assigning an operator instance to a
/// variable and passing a `task_id` keyword argument, e.g.
/// `extract = PythonOperator(\n    task_id="extract",\n)`.
fn extract_var_to_task_map(source: &str) -> HashMap<String, String> {
    let mut map = HashMap::new();
    let re = Regex::new(r#"(?s)(\w+)\s*=\s*\w*Operator\(.*?task_id\s*=\s*["']([^"']+)["']"#);
    if let Ok(re) = re {
        for cap in re.captures_iter(source) {
            map.insert(cap[1].to_string(), cap[2].to_string());
        }
    }
    map
}

/// Longest dependency chain (in nodes) starting at `node`, memoized.
fn longest_chain(
    node: &str,
    edges: &HashMap<String, Vec<String>>,
    memo: &mut HashMap<String, usize>,
    on_stack: &mut HashSet<String>,
) -> usize {
    if let Some(&cached) = memo.get(node) {
        return cached;
    }
    if on_stack.contains(node) {
        return 1;
    }
    on_stack.insert(node.to_string());
    let mut best = 1;
    if let Some(successors) = edges.get(node) {
        for successor in successors {
            best = best.max(1 + longest_chain(successor, edges, memo, on_stack));
        }
    }
    on_stack.remove(node);
    memo.insert(node.to_string(), best);
    best
}

/// Depth-first search for a back edge (cycle) starting at `node`.
///
/// `visiting` holds the nodes on the current DFS stack; re-entering one of
/// them means a cycle. `visited` memoizes fully-explored nodes so each node is
/// expanded once across the whole traversal.
fn has_cycle_from(
    node: &str,
    edges: &HashMap<String, Vec<String>>,
    visiting: &mut HashSet<String>,
    visited: &mut HashSet<String>,
) -> bool {
    if visited.contains(node) {
        return false;
    }
    if !visiting.insert(node.to_string()) {
        return true;
    }
    if let Some(successors) = edges.get(node) {
        for successor in successors {
            if has_cycle_from(successor, edges, visiting, visited) {
                return true;
            }
        }
    }
    visiting.remove(node);
    visited.insert(node.to_string());
    false
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

    #[test]
    fn test_max_depth_no_tasks_is_zero() {
        let parser = DagParser::new();
        assert_eq!(parser.calculate_max_depth("dag_id = 'x'\n"), 0);
    }

    #[test]
    fn test_max_depth_independent_tasks_is_one() {
        let parser = DagParser::new();
        let source = r#"
a = PythonOperator(task_id="a")
b = PythonOperator(
    task_id="b",
)
"#;
        // Two tasks, no dependencies between them.
        assert_eq!(parser.calculate_max_depth(source), 1);
    }

    #[test]
    fn test_max_depth_linear_chain() {
        let parser = DagParser::new();
        let source = r#"
extract = PythonOperator(
    task_id="extract",
)
transform = PythonOperator(
    task_id="transform",
)
load = PythonOperator(
    task_id="load",
)
extract >> transform >> load
"#;
        // Longest chain extract -> transform -> load = 3 tasks.
        assert_eq!(parser.calculate_max_depth(source), 3);
    }

    #[test]
    fn test_max_depth_diamond() {
        let parser = DagParser::new();
        let source = r#"
a = BashOperator(task_id="a")
b = BashOperator(
    task_id="b",
)
c = BashOperator(
    task_id="c",
)
d = BashOperator(
    task_id="d",
)
a >> b >> d
a >> c >> d
"#;
        // Longest chain is 3 tasks (a -> b -> d), not 4 (the diamond has no
        // path visiting both b and c).
        assert_eq!(parser.calculate_max_depth(source), 3);
    }

    #[test]
    fn test_max_depth_list_operand() {
        let parser = DagParser::new();
        let source = r#"
start = BashOperator(task_id="start")
a = BashOperator(task_id="a")
b = BashOperator(task_id="b")
finish = BashOperator(task_id="finish")
start >> [a, b] >> finish
"#;
        // start -> {a, b} -> finish, so longest chain = 3 tasks.
        assert_eq!(parser.calculate_max_depth(source), 3);
    }

    #[test]
    fn test_max_depth_set_upstream_and_downstream() {
        let parser = DagParser::new();
        let source = r#"
a = BashOperator(task_id="a")
b = BashOperator(task_id="b")
c = BashOperator(task_id="c")
b.set_upstream(a)
c.set_upstream(b)
"#;
        // b.set_upstream(a) => a -> b ; c.set_upstream(b) => b -> c.
        assert_eq!(parser.calculate_max_depth(source), 3);
    }

    #[test]
    fn test_max_depth_set_downstream() {
        let parser = DagParser::new();
        let source = r#"
a = BashOperator(task_id="a")
b = BashOperator(task_id="b")
c = BashOperator(task_id="c")
a.set_downstream(b)
b.set_downstream(c)
"#;
        // a.set_downstream(b) => a -> b ; b.set_downstream(c) => b -> c.
        assert_eq!(parser.calculate_max_depth(source), 3);
    }

    #[test]
    fn test_max_depth_left_shift_operator() {
        let parser = DagParser::new();
        let source = r#"
a = BashOperator(task_id="a")
b = BashOperator(task_id="b")
c = BashOperator(task_id="c")
c << b << a
"#;
        // c << b << a means a -> b -> c (still a 3-task chain).
        assert_eq!(parser.calculate_max_depth(source), 3);
    }

    #[test]
    fn test_detect_cycles_none_for_acyclic() {
        let parser = DagParser::new();
        let source = r#"
a = BashOperator(task_id="a")
b = BashOperator(task_id="b")
c = BashOperator(task_id="c")
a >> b >> c
"#;
        assert!(!parser.detect_cycles(source));
    }

    #[test]
    fn test_detect_cycles_finds_cycle() {
        let parser = DagParser::new();
        let source = r#"
a = BashOperator(task_id="a")
b = BashOperator(task_id="b")
c = BashOperator(task_id="c")
a >> b >> c >> a
"#;
        assert!(parser.detect_cycles(source));
    }

    #[test]
    fn test_detect_cycles_self_loop() {
        let parser = DagParser::new();
        let source = r#"
a = BashOperator(task_id="a")
a >> a
"#;
        assert!(parser.detect_cycles(source));
    }

    #[test]
    fn test_detect_cycles_via_set_upstream() {
        let parser = DagParser::new();
        let source = r#"
a = BashOperator(task_id="a")
b = BashOperator(task_id="b")
a.set_upstream(b)
b.set_upstream(a)
"#;
        // a's upstream is b, and b's upstream is a => a <-> b cycle.
        assert!(parser.detect_cycles(source));
    }
}
