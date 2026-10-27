# Audit Report: PyAirflowTester

## Overview
- **Type**: Python library + Rust crate (unwired) for Airflow/dbt analysis
- **Languages**: Python (primary), Rust (src/ unwired experiment)
- **Version**: 0.5.4
- **License**: Apache-2.0
- **Purpose**: Static analysis, risk scoring, dependency graph for Airflow DAGs and dbt

## Architecture
- **Python**: Core in `python/pyairflowtester/`, CLI, web UI (optional)
- **Rust**: `src/*.rs` present but not shipped/built, unwired PyO3 experiment
- **Analysis**: AST parsing, graph building, rule engine (33 rules)

## Entry Points
- CLI: `pyairflowtester`
- Python API

## Dependencies
- click, rich (core)
- Optional: sqlglot (lineage), fastapi/uvicorn/jinja2 (web)

## Security Observations
- Static analysis only - low runtime risk
- No network calls by default
- Web UI local if used

## Tests/CI
- pytest with coverage, tests/ exist
- CI badge present

## Findings

| Severity | Finding | Evidence | Impact | Root Cause Hypothesis | Recommendation |
|----------|---------|----------|--------|----------------------|---------------|
| Medium | Rust code present but unwired/not shipped | README states clearly | Confusion, dead code in repo | Experiment abandoned/in progress | Remove or clearly isolate; don't mislead |
| Medium | "Analyzer/connect" path stubbed | README states | Incomplete feature | Planned but not implemented | Document as not implemented |
| Low | Pure Python only in shipped package | pyproject says hatchling builds python/ | OK if intentional | Design choice | Fine as-is |

## Strengths
- Comprehensive rule set
- Good CI integration (SARIF)
- Clear documentation of limitations
- Differentiation from similar tools

## Limitations
- No live runtime correlation
- Not a test runner
- Rust experiment not integrated

## Prioritized Recommendations
1. **Medium**: Clean up unwired Rust code or integrate it
2. **Low**: Complete or remove stubbed features
3. **Low**: Add more tests for edge cases
