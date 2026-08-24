# PyAirflowTester: Airflow & dbt Static Analysis + Dependency Intelligence

Static analysis and dependency-graph tooling for Airflow DAGs and dbt projects, plus a
library-level dependency intelligence toolkit (impact analysis, blast radius, risk scoring,
observability). Ships as a pure-Python CLI.

## What actually works today

- **`pyairflowtester scan`** — runs 33 static analysis rules against Airflow DAG source files,
  a dbt `manifest.json`, and/or an `airflow.cfg`, and reports violations (security secrets,
  hardcoded connections, missing SLAs, circular dependencies, config misconfigurations, etc).
- **`pyairflowtester rules`** — lists the full rule catalog.
- **`pyairflowtester score`** — aggregate risk score from scan findings.
- **`pyairflowtester dependency ...`** — build a unified dependency graph from DAG files and a
  dbt manifest, then query impact/blast-radius/lineage/cycles/orphans/risk-score over it.
- The `pyairflowtester.dependency_intelligence` package (usable as a library, see examples
  below) for ownership tracking, schema-evolution tracking, SLA validation, test-coverage
  analysis, anomaly detection, recommendations, and observability primitives
  (metrics/alerts/events/dashboards) — these operate on the graph you build, not on a live
  system.

## What does not work (yet) — please read before relying on this

- **Runtime correlation (`Analyzer` class) is not implemented.** It's meant to correlate
  findings against a live Airflow metadata database and dbt run history, but doing that
  honestly requires a real Airflow/dbt instance to build and validate against. Every
  `Analyzer` method (and the `pyairflowtester connect` CLI command) raises
  `AnalyzerNotImplementedError` with a clear message rather than silently returning `[]` and
  pretending nothing was found. This is planned future work, not a working feature.
- **The Rust core (`src/*.rs`, built via PyO3) is not wired into the CLI.** The Python
  package ships as pure Python and does not require Rust or `maturin` to install or run.
  The Rust crate exists as a separate, independent reimplementation of some rule/parsing/
  scoring logic; `python/pyairflowtester/__init__.py` will opportunistically import it if
  you build it yourself (`maturin develop`), but nothing in the CLI path uses it, and it is
  not built or shipped as part of the published package. Treat it as an experiment, not a
  supported acceleration layer.
- **The `dependency_intelligence` "Phase 3" intelligence engines (`FailurePredictionEngine`,
  `HealthScoreCalculator`) don't actually consult real test-coverage data, despite the
  comments suggesting they should.** `FailurePredictionEngine.predict_node_failure` hardcodes
  `test_count = 0` for every node (so "no test coverage" always contributes to the failure
  score, regardless of what you've fed `TestCoverageAnalyzer`) and assumes a fixed 30-day
  failure window. `HealthScoreCalculator._calculate_test_score` always returns the same fixed
  value (10.0) regardless of the graph. They're importable and exported, but their
  test-coverage inputs are not wired to the real `TestCoverageAnalyzer` yet — treat their
  output as illustrative, not measured. Everything else under "Dependency Intelligence" below
  (ownership, schema evolution, SLA validation, test-coverage analysis via
  `TestCoverageAnalyzer`, anomaly detection, observability) does operate on real data you feed
  it.

## Installation

```bash
pip install pyairflowtester
# or with uv
uv pip install pyairflowtester

# Verify installation
pyairflowtester --version
```

Pure Python — no Rust toolchain required.

For development:

```bash
git clone https://github.com/mullassery/pyairflowtester.git
cd pyairflowtester
pip install -e ".[dev]"
```

## Static Analysis: `scan`

```bash
# Scan DAGs, a dbt project, and/or airflow.cfg
pyairflowtester scan . --dags dags/ --dbt dbt/ --airflow-cfg airflow.cfg

# Output formats
pyairflowtester scan . --format json --output results.json
pyairflowtester scan . --format html --output report.html
pyairflowtester scan . --format sarif --output results.sarif  # For GitHub code scanning

# Filter results
pyairflowtester scan . --dags dags/ --severity critical
pyairflowtester rules --category security
```

Rule catalog (33 rules, see `pyairflowtester rules` for the live list):

- **AFW001-AFW015** — DAG source-code rules: circular dependencies (real graph-cycle
  detection over parsed `>>`/`<<`/`set_upstream`/`set_downstream` edges, not a regex
  backreference hack), missing SLAs, expensive imports, excessive task counts, risky
  catchup config, default pool usage, hardcoded connection IDs, **hardcoded secrets**,
  excessive retries, sensor timeouts, branch complexity, missing docs, missing alerting,
  deprecated operators.
- **DBT001-DBT003** — dbt manifest rules: missing tests, redundant tests, untested
  high-importance models (derived from the manifest's actual `test.*` nodes and their
  `depends_on`/`attached_node`, not a nonexistent manifest field).
- **CFG001-CFG015** — `airflow.cfg` audit rules: executor choice, pool sizing, concurrency,
  queueing, log retention, encryption, TLS, RBAC, scheduler/worker settings, log storage,
  backups, DAG folder location.

Every rule is evaluated in isolation: if one rule throws, it logs a warning and the rest of
the rules still run and still report their findings for that file.

## Dependency Intelligence

### CLI

```bash
pyairflowtester dependency build --dags dags/ --dbt-manifest dbt/target/manifest.json
pyairflowtester dependency impact <node_id> --depth 10
pyairflowtester dependency lineage --dags dags/
pyairflowtester dependency blast-radius -n <node_id>
pyairflowtester dependency detect-cycles --dags dags/
pyairflowtester dependency detect-orphans --dags dags/
pyairflowtester dependency risk-score --dags dags/ --top 20
```

### As a library

```python
from pyairflowtester.dependency_intelligence import (
    UnifiedGraphBuilder,
    ImpactAnalysisEngine,
    BlastRadiusEngine,
)

# Build a unified graph from DAG files + a dbt manifest
graph = UnifiedGraphBuilder.build_unified_graph(
    dag_files=["dags/my_dag.py"],
    dbt_manifest="dbt/target/manifest.json",
)

# Analyze impact of changing a node
impact = ImpactAnalysisEngine(graph).analyze("dag_my_dag")
print(f"Impact Score: {impact.impact_score:.1%}")
print(f"Impacted Nodes: {len(impact.impacted_nodes)}")

# Calculate deployment risk
blast = BlastRadiusEngine(graph).analyze(["dag_my_dag"])
print(f"Blast Radius: {blast.blast_radius} nodes")
print(f"Safe to Deploy: {'Yes' if blast.deployable else 'No'}")
```

```python
from pyairflowtester.dependency_intelligence import RiskScoringEngine

engine = RiskScoringEngine(graph)
scores = engine.score_all_nodes()

high_risk = sorted(scores.items(), key=lambda x: x[1].risk_score, reverse=True)[:10]
for node_id, score in high_risk:
    print(f"{node_id}: Risk {score.risk_score:.1f}/10")
```

```python
from pyairflowtester.dependency_intelligence import (
    MetricsCollector, AlertManager, EventLogger, DashboardBuilder,
)

# These operate on data you feed them (e.g. from your own Airflow listener/webhook),
# not on a live connection this library establishes itself.
metrics = MetricsCollector()
alerts = AlertManager(graph)
events = EventLogger(graph)

events.log_execution(
    node_id="fact_orders", status="success", duration_ms=1250,
    start_time=..., end_time=...,
)
alerts.set_threshold("fact_orders", "execution_time", warning=5000, critical=10000)

builder = DashboardBuilder(graph, metrics, alerts, events)
dashboard = builder.build_health_dashboard()
```

## Architecture

Two real, independent things live in this repo:

1. **The Python CLI (`python/pyairflowtester/`)** — this is what `pip install pyairflowtester`
   ships and what every command above actually runs: `Scanner` (33 rules), `ReportGenerator`,
   `Scorer`, and the `dependency_intelligence` package (graph model, parsers, analytics
   engines, observability primitives). This is the supported, tested path.
2. **A Rust crate (`src/*.rs`)** — a separate, partial reimplementation of some of the same
   rule/parsing/scoring logic using PyO3 bindings (`pyairflowtester._core`). It is **not**
   built or used by the published package or the CLI. `__init__.py` imports it opportunistically
   and falls back to `None` if it isn't present, which is the normal case for anyone who just
   `pip install`s this package. Building the extension yourself (`maturin develop`) does not
   change the CLI's behavior — nothing in the CLI calls into it.

The `Analyzer` class (runtime correlation against live Airflow/dbt) is a stub that raises
`AnalyzerNotImplementedError` — see "What does not work (yet)" above.

## Status

**Proof of concept, actively fixed up.** The static-analysis CLI path (`scan`, `rules`,
`score`, `dependency ...`) works end-to-end and is covered by an automated test suite.
Runtime correlation is explicitly not implemented (fails fast, doesn't fake results). The
Rust core is not part of the supported path.

- Test suite: `python/tests/`, run with `pytest` from the repo root — **163 tests, 0
  failing** (verify yourself: `pytest python/tests/ -v`).
- Static rules: 33, all wired into `scan` (previously most of the catalog — the
  `dag_advanced.py` rules including secrets detection, and all of `config.py` — was defined
  but never actually invoked by `scan`).

## CLI Reference

```bash
pyairflowtester scan . --dags dags/ --dbt dbt/ --airflow-cfg airflow.cfg --format html
pyairflowtester score . --compare main
pyairflowtester rules --category reliability --severity critical
pyairflowtester dependency build --dags dags/ --dbt-manifest manifest.json
pyairflowtester dependency impact <node_id> --depth 10
pyairflowtester dependency lineage --format mermaid
pyairflowtester dependency blast-radius -n <node_id>
pyairflowtester dependency detect-cycles
pyairflowtester dependency detect-orphans
pyairflowtester dependency risk-score --top 20
pyairflowtester connect --airflow-home $AIRFLOW_HOME  # currently: reports "not implemented"
```

## Requirements

- Python 3.10+
- For Airflow integration: Airflow 2.0+ (only used to shape the DAG source patterns the
  rules look for; Airflow itself is not a runtime dependency)
- For dbt integration: a dbt `manifest.json` (dbt itself is not a runtime dependency)

## Roadmap

Honestly scoped, in priority order:

- Runtime correlation (`Analyzer`): connect to a live Airflow metadata DB and dbt run
  history, replace the current fail-fast stub with real analysis. Needs a live
  Airflow/dbt instance to build and validate against.
- Decide the Rust core's fate: either wire `pyairflowtester._core` into the CLI for real
  (bigger architectural change — would need the two rule/parsing implementations
  reconciled) or drop it to avoid maintaining two parallel implementations.
- Broader dbt manifest coverage, more config-audit rules, richer report formats.
- Tiered caching (L1 Memory, L2 Redis, L3 SQLite, L4 DuckDB): currently design-only —
  `DEPENDENCY_CACHING_STRATEGY.md` sketches the architecture (including Redis pub/sub
  invalidation) but none of it is implemented in `python/pyairflowtester/`. If/when
  built, use event-driven invalidation rather than TTL-only expiration, and add locking
  around concurrent multi-process cache writes from the start.
- Runtime-import fallback for dynamic DAGs: the AST-based parser
  (`dependency_intelligence/parsers.py`) only pattern-matches literal `DAG(...)`/
  operator calls, so DAGs built via factory functions, dynamic loops, or `exec`/`eval`
  are invisible to it. A sandboxed runtime-import fallback (e.g. parsing serialized DAG
  bundles) would close that blind spot.

## Contributing

Contributions welcome. Please submit pull requests to GitHub.

## License

Proprietary. See LICENSE file for details.

## Contact

For issues, questions, or feature requests: https://github.com/mullassery/pyairflowtester/issues
