# PyAirflowTester: Unified Airflow + dbt Reliability Platform

[![CI/CD](https://github.com/mullassery/pyairflowtester/workflows/CI%2FCD/badge.svg)](https://github.com/mullassery/pyairflowtester/actions)
[![Code Coverage](https://codecov.io/gh/mullassery/pyairflowtester/branch/main/graph/badge.svg)](https://codecov.io/gh/mullassery/pyairflowtester)
[![PyPI](https://img.shields.io/pypi/v/pyairflowtester.svg)](https://pypi.org/project/pyairflowtester/)

A **correlation-first reliability and quality platform** that unifies static analysis and runtime monitoring for Airflow DAGs and dbt projects.

## Features

### 🔍 Static Analysis (Shift-Left)
- **DAG Validation:** Circular dependencies, dynamic DAGs, expensive imports, parse time analysis
- **dbt Analysis:** Missing tests, redundant tests, untested models, test failure analysis
- **Configuration Auditing:** Detect misconfigurations and anti-patterns before deployment
- **35+ Built-in Rules** across reliability, performance, maintainability, security, and cost categories

### ⚡ Runtime Analysis (Production)
- **Failure Pattern Detection:** Identify chronic failures, hotspots, and cascading failures
- **Correlation Engine:** Automatic root cause analysis linking source code to failures
- **Blast Radius Analysis:** Understand downstream impact of failures
- **Failure Prediction:** Predict failures 7 days in advance using historical data

### 📊 Intelligence & Scoring
- **Multi-Dimensional Risk Scores:** Reliability, performance, maintainability, security, cost
- **Health Scorecards:** Comprehensive view of pipeline health
- **Trend Analysis:** Track improvements and degradation over time

### 🔌 OpenTelemetry Integration
- Export to 6+ observability platforms: Datadog, New Relic, Honeycomb, Splunk, Dynatrace, Elastic
- Alert routing to PagerDuty, Slack, email
- Full trace instrumentation

### 📈 Reporting
- **CLI Reports:** Rich terminal output with colors and tables
- **Multiple Formats:** JSON, HTML, Markdown, SARIF (GitHub integration), CSV
- **Custom Templates:** Jinja2-based report customization

## Installation

```bash
pip install pyairflowtester
```

### Development Installation

```bash
git clone https://github.com/mullassery/pyairflowtester.git
cd pyairflowtester
pip install -e ".[dev,otel]"
```

## Quick Start

### Scan Airflow DAGs and dbt Projects

```bash
# Scan current directory
pyairflowtester scan .

# Scan specific paths
pyairflowtester scan --dags /path/to/dags --dbt /path/to/dbt

# Filter by severity
pyairflowtester scan . --severity high

# Generate HTML report
pyairflowtester scan . --format html --output report.html
```

### Calculate Risk Scores

```bash
# Score your pipeline
pyairflowtester score .

# Compare to baseline
pyairflowtester score . --compare main
```

### List Rules

```bash
# Show all rules
pyairflowtester rules

# Filter by category
pyairflowtester rules --category reliability

# Filter by severity
pyairflowtester rules --severity critical
```

### Connect to Live Airflow (Runtime Analysis)

```bash
# Auto-detect Airflow instance
pyairflowtester connect --airflow-home /path/to/AIRFLOW_HOME

# Manual database connection
pyairflowtester connect --airflow-db postgresql://user:pass@localhost/airflow
```

## Architecture

```
┌─────────────────────────────────┐
│   CLI / API / Dashboards        │
├─────────────────────────────────┤
│                                 │
│  Artifact Analysis    Runtime   │
│  (Shift-Left)         (Prod)    │
│  • DAG Parser         • DB       │
│  • dbt Analyzer       • Collector│
│  • Config Audit       • Logs     │
│                                 │
├─────────────────────────────────┤
│  Correlation & Analysis Engine  │
│  • Failure Attribution          │
│  • Root Cause Analysis          │
│  • Blast Radius Calc            │
│  • Risk Scoring                 │
├─────────────────────────────────┤
│  Storage Layer                  │
│  • PostgreSQL                   │
│  • TimescaleDB                  │
│  • S3/Cloud                     │
└─────────────────────────────────┘
```

## Rules

### DAG Rules (AFW)
- **AFW001:** Circular dependencies (Critical)
- **AFW002:** Missing SLA (High)
- **AFW003:** Expensive imports (Medium)
- **AFW004:** Parse time analysis (Medium)
- ... 15+ more DAG rules

### dbt Rules (DBT)
- **DBT001:** Missing tests (High)
- **DBT002:** Redundant tests (Low)
- **DBT003:** Untested public models (Medium)
- ... 20+ more dbt rules

### Configuration Rules (CFG)
- **CFG001:** Executor misconfiguration
- **CFG002:** Pool/queue bottlenecks
- ... 15+ more configuration rules

## Python API

```python
from pyairflowtester import Scanner, Analyzer, ReportGenerator

# Artifact analysis
scanner = Scanner()
violations = scanner.scan_dags(Path("dags"))
violations += scanner.scan_dbt(Path("dbt"))

# Generate report
generator = ReportGenerator()
generator.generate("html", violations, Path("report.html"))

# Runtime analysis
analyzer = Analyzer(airflow_db="postgresql://...")
analyzer.connect()
failures = analyzer.analyze_dag_failures("my_dag")
hotspots = analyzer.detect_hotspots()
blast_radius = analyzer.calculate_blast_radius("my_dag", source_type="dag")

# Scoring
from pyairflowtester.scoring import Scorer
scorer = Scorer()
risk_score = scorer.calculate_risk_score(violations)
risk_level = scorer.categorize_risk(risk_score)
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: PyAirflowTester Scan
  uses: mullassery/pyairflowtester-action@v1
  with:
    dags-path: ./dags
    dbt-path: ./dbt
    format: sarif
```

### Pre-commit Hook

```yaml
repos:
  - repo: https://github.com/mullassery/pyairflowtester
    rev: v0.1.0
    hooks:
      - id: pyairflowtester
        args: [--severity, high]
```

## Configuration

Create `.pyairflowtester.yml`:

```yaml
artifacts:
  dags_path: ./dags
  dbt_path: ./dbt
  scan_on_commit: true

runtime:
  airflow_db: postgresql://localhost/airflow
  retention_days: 30

rules:
  enabled_categories:
    - reliability
    - performance
  min_severity: medium
  exclude_rules:
    - DBT002

scoring:
  weights:
    reliability: 0.5
    performance: 0.3
    maintainability: 0.2

otel:
  enabled: true
  exporter: datadog
  sample_rate: 1.0
```

## Development

### Build

```bash
# Build Rust extension
cargo build --release

# Build Python wheel
maturin build --release
```

### Test

```bash
# Rust tests
cargo test

# Python tests
pytest python/tests/

# Integration tests
pytest python/tests/integration/

# Coverage
pytest --cov=pyairflowtester
```

### Documentation

```bash
pip install sphinx sphinx-rtd-theme
cd docs
make html
```

## Roadmap

- **v0.1 (Q4 2026):** MVP - DAG + dbt analysis, 35 rules, basic risk scoring
- **v0.2 (Q1 2027):** Runtime analysis, correlation engine, OTEL metrics
- **v0.3 (Q2 2027):** Prediction & anomalies, CLI reports, Python API, OTEL tracing
- **v1.0 (Q3 2027):** Enterprise features, multi-tenant, RBAC, 6+ OTEL platforms
- **v1.1+ (2028):** IDE plugins, advanced ML, cost attribution, more platforms

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/mullassery/pyairflowtester.git
cd pyairflowtester
pre-commit install
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest python/tests/ -v
cargo test --verbose
```

## License

PyAirflowTester is a proprietary product. See [LICENSE](LICENSE) for terms and conditions.

## Support

- 📖 [Documentation](https://pyairflowtester.readthedocs.io)
- 💬 [GitHub Discussions](https://github.com/mullassery/pyairflowtester/discussions)
- 🐛 [Issue Tracker](https://github.com/mullassery/pyairflowtester/issues)
- 💼 [Commercial Support](mailto:support@pyairflowtester.com)

## Acknowledgments

Inspired by SonarQube, Ruff, Checkov, Monte Carlo, and Datadog.
