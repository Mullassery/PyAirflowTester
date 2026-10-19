# PyAirflowTester

Static analysis, dependency intelligence, and risk scoring for Airflow DAGs and dbt projects.

> **Not to be confused with [PyDBTGuard](https://github.com/Mullassery/PyDBTGuard) or [PyBeamGuard](https://github.com/Mullassery/PyBeamGuard):** PyAirflowTester validates Airflow DAGs (and dbt runs); PyDBTGuard analyzes dbt manifests; PyBeamGuard analyzes Beam/Dataflow pipelines.

## Which project do I need?

Part of the Mullassery open-source family. These tools have similar names — here is the short version of who does what:

| If you need to… | Use |
| --- | --- |
| Build a repository's dependency graph and match it against vulnerability advisories (Python, Rust, Node, containers) | [PyDeepMesh](https://github.com/Mullassery/PyDeepMesh) |
| Understand *why* a Python dependency exists, who added it, and whether it is actually used | [PyDependencyCheck](https://github.com/Mullassery/PyDependencyCheck) |
| Statically analyze a **dbt** project (risky tests, test blast radius, cost) | [PyDBTGuard](https://github.com/Mullassery/PyDBTGuard) |
| Statically analyze **Apache Beam / Dataflow** pipelines (cost, hot keys, reliability) | [PyBeamGuard](https://github.com/Mullassery/PyBeamGuard) |
| Validate **Airflow** DAGs and dbt runs | [PyAirflowTester](https://github.com/Mullassery/PyAirflowTester) |
| Simulate cascading-failure **blast radius** across infrastructure, data pipelines, and AI systems | [PyBlastRadius](https://github.com/Mullassery/PyBlastRadius) |
| Check the **quality of the data itself** at runtime (schema, drift, anomalies) | [StatGuardian](https://github.com/Mullassery/StatGuardian) |
| Discover **devices, services, and vulnerabilities on a network** | [PyNetworkIntel](https://github.com/Mullassery/PyNetworkIntel) |
| Discover and score **API security** risk (real traffic, agent/MCP, Cedar policy) | [PyAPICheck](https://github.com/Mullassery/PyAPICheck) |
| Trace and root-cause **AI agent** failures | [PyAgentHound](https://github.com/Mullassery/PyAgentHound) |
| Diagnose **RAG retrieval** failures | [PyVectorHound](https://github.com/Mullassery/PyVectorHound) |
| Orchestrate **local, dependency-aware tasks** (DAG scheduler + content-addressed cache) | [PyTaskWireCheck](https://github.com/Mullassery/PyTaskWireCheck) |

[Browse all projects →](https://github.com/Mullassery?tab=repositories)

## What it is

PyAirflowTester helps you catch reliability and security issues before deployment by statically analyzing Airflow DAGs, dbt manifests, and `airflow.cfg`. It builds a unified dependency graph to understand blast radius and impact, computes aggregate risk scores, and exports findings in formats suitable for CI (including SARIF for GitHub code scanning).

## Features / Highlights

- **Static analysis**: 33 rules covering DAGs, dbt manifests, and Airflow configuration (secrets, SLAs, cycles, config issues, etc.).
- **Parsed DAG metadata**: AST-based task depth (longest dependency chain), dynamic-DAG detection (loops, `globals()`, task groups, dynamic task mapping), and external systems referenced by operator classes, `conn_id`, SQL, or imports.
- **Unified dependency graph**: Combines Airflow DAG edges with dbt lineage from `manifest.json`.
- **Impact & blast radius**: Understand what breaks downstream if a node changes.
- **Risk scoring**: Aggregate 0-100 risk score with filtering by severity.
- **CI-friendly**: JSON, HTML, and SARIF output for GitHub code scanning.
- **Web dashboard**: Optional FastAPI/uvicorn dashboard (`serve`) to visualize graph and findings.
- **Library API**: Dependency intelligence primitives for programmatic use (impact, blast radius, risk, observability helpers).

## Who it's for / Use cases

- **CI gating**: Fail builds on critical findings or low risk scores.
- **Pre-deployment checks**: Assess blast radius before changing high-impact nodes.
- **Security reviews**: Catch hardcoded secrets, risky configs, and missing guardrails.
- **dbt + Airflow alignment**: See end-to-end dependencies across orchestration and transformation.
- **Technical debt tracking**: Identify orphans, cycles, and untested/high-importance nodes.

## What it is not

- **Not a live runtime correlator**: The `Analyzer`/`connect` path for correlating against live Airflow metadata or dbt run history is explicitly stubbed (`AnalyzerNotImplementedError`).
- **Not a test runner**: It analyzes structure and metadata, not executes DAGs or dbt tests.
- **Pure Python only (shipped)**: The installable package is built with hatchling from `python/pyairflowtester` and contains no compiled extension. `src/*.rs` is an unwired PyO3 experiment, not part of the wheel, CLI, or supported API. See [Rust crate status](#rust-crate-status-not-shipped).
- **Alpha maturity**: v0.5.4 - core scanning, graph analysis, and scoring are working; runtime correlation is planned.

## Rust crate status (not shipped)

`src/*.rs` is an independent PyO3 experiment, not a "core" used by the Python package. It is not built by `pyproject.toml` (hatchling packages only `python/pyairflowtester`), not imported by the CLI, and not installed in the wheel. The audit below (2026-10-20) is why it stays unwired:

| Module | What it contains | Assessment |
| --- | --- | --- |
| `dag_parser.rs` | Regex-based DAG parser: DAG ID, task IDs, `>>`/`<<` and `set_upstream`/`set_downstream` edges, longest task chain, cycle detection, dynamic-DAG detection, expensive imports, external dependencies. 16 unit tests. | Real code, but duplicates the Python AST parser (`dependency_intelligence/parsers.py`), the new `dag_parser.py` metadata parser, and rules AFW001/AFW003. Bare `cargo test` does not link on macOS arm64 in this configuration, so these tests do not run in the supported dev flow. |
| `dbt_parser.rs` | Manifest, catalog, and run-results readers; model/test/lineage extraction. | Real but only constructor tests (3). Duplicates the Python manifest parser and uses substring matching for lineage, which can create false edges. |
| `scoring.rs` | Risk, health, trend, and priority arithmetic. | Duplicates `scoring.py`, and its risk formula still has the pre-0.5.2 inverted severity-to-risk behavior. |
| `rule_engine.rs` | Generic `Rule` trait, enums, and engine. | Framework only; no production rules are implemented. Python has 33 concrete rules. |
| `lib.rs` | PyO3 wrappers. | Not usable as an API: `PyRuleEngine` cannot register or evaluate rules, `evaluate_rules` returns fabricated `info` findings, and `PyScorer` exposes only one method. |

Decision: do not ship or expose it. No Rust-only behavior is both unique and trustworthy. The three metadata fields Python previously lacked (`max_task_depth`, `dynamic_dag_detected`, `external_dependencies`) are now implemented by the Python AST parser in `python/pyairflowtester/dag_parser.py` and are exposed through the public `DagParser`/`DagDefinition` API and the `parse-dags` CLI. Shipping PyO3 would require compiled wheels and a Rust toolchain for no user-facing benefit, and exposing the current stubs would be misleading. The crate remains in the repository only as an unwired experiment; it is not on the release or integration path.

## Project status

Version 0.5.4. Core commands (`scan`, `score`, `rules`, `dependency ...`, `serve`) are functional. The runtime correlation feature is stubbed (not implemented). See [ROADMAP_HONEST.md](ROADMAP_HONEST.md) for details.

## Installation

```bash
pip install pyairflowtester
```

With web dashboard:

```bash
pip install "pyairflowtester[web]"
```

From source:

```bash
git clone https://github.com/mullassery/pyairflowtester.git
cd pyairflowtester
pip install -e ".[dev]"
```

Requires Python 3.10+.

## Quick start

```bash
# Scan current directory for DAGs, dbt, airflow.cfg
pyairflowtester scan . --dags dags/ --dbt dbt/ --airflow-cfg airflow.cfg

# Get aggregate risk score
pyairflowtester score . --dags dags/

# List all rules
pyairflowtester rules

# Parse DAG metadata: max task depth, dynamic DAGs, external systems
pyairflowtester parse-dags dags/ --format json

# Build dependency graph and analyze blast radius
pyairflowtester dependency build --dags dags/ --dbt-manifest dbt/target/manifest.json
pyairflowtester dependency blast-radius -n dag_my_dag

# Launch web dashboard
pyairflowtester serve --port 8080
```

### Programmatic usage

```python
from pyairflowtester import DagParser

dag = DagParser().parse_file("dags/my_dag.py")
print(dag.dag_id, dag.max_task_depth, dag.dynamic_dag_detected)
print(dag.external_dependencies)
```

```python
from pyairflowtester.dependency_intelligence import (
    UnifiedGraphBuilder,
    ImpactAnalysisEngine,
    BlastRadiusEngine,
)

graph = UnifiedGraphBuilder.build_unified_graph(
    dag_files=["dags/my_dag.py"],
    dbt_manifest="dbt/target/manifest.json",
)

impact = ImpactAnalysisEngine(graph).analyze("dag_my_dag")
print(f"Impact score: {impact.impact_score:.1%}, impacted: {len(impact.impacted_nodes)}")

blast = BlastRadiusEngine(graph).analyze(["dag_my_dag"])
print(f"Blast radius: {blast.blast_radius} nodes, deployable: {blast.deployable}")
```

## Known issues and deferred work

**Blocked / failed:**
- Runtime correlation via Airflow REST/dbt run_results.

**Rejected / deferred:**
- A test runner.

Full shipped/blocked/rejected detail: [`QUEUE_STATUS.md`](QUEUE_STATUS.md).

## Documentation

- [ROADMAP_HONEST.md](ROADMAP_HONEST.md) - Known limitations and planned work
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md)

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

## OpenLineage runtime ingestion

Ingest OpenLineage events emitted by Airflow/dbt/Spark into a local SQLite
lineage store:

```bash
pyairflowtester openlineage events.ndjson --db runtime.sqlite
pyairflowtester openlineage events.ndjson --db runtime.sqlite --format json
```

```python
from pyairflowtester.openlineage import ingest_files

summary = ingest_files(["events.ndjson"], "runtime.sqlite")
print(summary.runs, summary.jobs, summary.datasets, summary.edges)
```

JSON arrays, single events and NDJSON are supported. Runs are idempotent by
`(run_id, event_type)`, and job/dataset edges are deduplicated. This is an
adapter over the Apache-2.0 OpenLineage schema, not a fork.

