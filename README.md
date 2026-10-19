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
- **Pure Python by default**: A Rust core exists in `src/` but is not wired into the CLI and not shipped; building it is optional.
- **Alpha maturity**: v0.5.2 - core scanning, graph analysis, and scoring are working; runtime correlation is planned.

## Project status

Version 0.5.2. Core commands (`scan`, `score`, `rules`, `dependency ...`, `serve`) are functional. The runtime correlation feature is stubbed (not implemented). See [ROADMAP_HONEST.md](ROADMAP_HONEST.md) for details.

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

# Build dependency graph and analyze blast radius
pyairflowtester dependency build --dags dags/ --dbt-manifest dbt/target/manifest.json
pyairflowtester dependency blast-radius -n dag_my_dag

# Launch web dashboard
pyairflowtester serve --port 8080
```

### Programmatic usage

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

## Queue status

Shipped, blocked/failed, and rejected work for this repository is documented in
[`QUEUE_STATUS.md`](QUEUE_STATUS.md).

## Documentation

- [ROADMAP_HONEST.md](ROADMAP_HONEST.md) - Known limitations and planned work
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md)

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
