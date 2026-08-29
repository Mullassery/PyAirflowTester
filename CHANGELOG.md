# Changelog

All notable changes to PyAirflowTester are documented in this file.

## [0.5.0]

### Added

- **Web dashboard (`pyairflowtester serve`)** — `python/pyairflowtester/web/app.py`.
  The unified graph engine (DAG/dbt node analytics, `DashboardBuilder`) was
  previously CLI-only; `DashboardBuilder`'s output is now also served as a real
  browsable FastAPI app (node list, per-node dashboard, health dashboard),
  rendered as actual HTML tables rather than a JSON dump. Optional `web` extra
  (`fastapi`, `uvicorn`, `jinja2`) — `pip install pyairflowtester[web]`.

## [0.4.0]

### Added

- **Tiered cache (L1 in-memory + L3 SQLite)** — `dependency_intelligence/cache.py`.
  `DEPENDENCY_CACHING_STRATEGY.md` sketched a 4-layer design (L1 Memory, L2
  Redis, L3 SQLite, L4 DuckDB) that had never actually been implemented in
  code. `InMemoryCache` (thread-safe LRU with real per-entry TTL) and
  `SqliteCache` (WAL-mode, multi-process-safe persistent cache) are now
  real, plus a `TieredCache` combining them with event-driven invalidation
  (`register_invalidation_rule`/`emit`) instead of relying on TTL expiry
  alone. `DependencyGraphEngine` takes an optional `cache=` param and uses
  it for `detect_cycles()`/`get_strongly_connected_components()`, keyed by
  a content hash of the graph so a changed graph never serves stale
  results — and, with a `SqliteCache`, results now survive across separate
  process invocations, which nothing in this codebase could do before.
  L2 (Redis) and L4 (DuckDB) are still not implemented — this ships two
  real tiers, not four faked ones.
- **Sandboxed runtime-import fallback for dynamic DAGs** —
  `dependency_intelligence/runtime_import.py`. The static AST parser
  (`AirflowDAGParser`) only recognizes literal `DAG(...)`/`*Operator(...)`
  calls, so it misses DAGs built via factory functions, dynamic loops, or
  `exec`/`eval`. `parse_dag_via_runtime_import()` actually imports the DAG
  file in an isolated subprocess (resource-limited, timeout-guarded) and
  reads back the real, fully-resolved task graph from actual `airflow.models.DAG`
  objects — correct regardless of how dynamically the tasks were
  constructed. Opt-in and requires the optional `airflow` package, per this
  project's existing design of not taking Airflow on as a hard runtime
  dependency. `parse_dag_file_with_fallback()` tries the fast static parser
  first and only pays for the subprocess import when that comes back empty.

## [0.3.1] - 2026-08-23

### Real fix: dependency-intelligence health/risk scoring no longer hardcoded

`FailurePredictionEngine.predict_node_failure` and
`HealthScoreCalculator._calculate_test_score` (in
`dependency_intelligence/intelligence.py`) previously ignored the actual
graph and returned fake, hardcoded test-coverage figures regardless of
input (`test_count = 0` always; a fixed `10.0` score always). Both now
consult the real `TestCoverageAnalyzer` already used correctly elsewhere
in the module, so failure predictions and health scores actually reflect
each node's real test coverage.

Also fixed several CI-only issues (Rust clippy/lint debt in the optional
`_core` extension, a broken security-scan action, an unguarded
integration-test job) that don't affect the shipped pure-Python package.

## [0.3.0] - 2026-08-15

### First public PyPI release, and a correctness pass on the primary `scan` workflow

This release fixes the primary advertised workflow (`pyairflowtester scan`), which was
completely broken: the very first DAG rule that ran (`CircularDependencyRule`) crashed with
`re.error: invalid group reference 1` on every invocation, and that exception was caught by
a single try/except wrapped around the *entire* per-file rule loop, silently discarding every
other rule's findings for that file too — including the security-critical secrets-detection
rule. Additionally, most of the rule catalog the CLI's `rules` subcommand advertised was
never actually wired into `scan` at all.

### Fixed

- `CircularDependencyRule` (AFW001): replaced the broken backreference regex with real
  graph-cycle detection over parsed `>>`/`<<`/`set_upstream`/`set_downstream` edges.
- `Scanner.scan_dags`/`scan_dbt`/`scan_config`: exception handling is now isolated per rule
  instead of per file, with a clear warning logged when a rule fails, so one bad rule can no
  longer suppress every other rule's findings.
- Wired the 11 previously-unwired `dag_advanced.py` rules (AFW005-AFW015, including
  `SecretsInCodeRule` and `HardcodedConnectionRule`) and all 15 `config.py` rules
  (CFG001-CFG015, via a new `Scanner.scan_config()` / `--airflow-cfg` scan option) into the
  actual scan path.
- Resolved a naming collision: two unrelated classes were both named
  `PoolConfigurationRule` and silently shadowed each other on import. Renamed to
  `SourceCodePoolConfigurationRule` (AFW007) and `AirflowCfgPoolConfigurationRule` (CFG002).
- `AirflowDAGParser.parse_dag_code`: now extracts `dag_id` from the idiomatic positional
  form `DAG('my_dag', ...)`, not just the `dag_id=` keyword form.
- `UntestedModelRule` (DBT003): derives real test counts from the manifest's `test.*` nodes
  instead of a `test_dependencies` field that dbt's manifest schema doesn't actually have.
- `Analyzer` (runtime correlation against live Airflow/dbt): every method now raises
  `AnalyzerNotImplementedError` with a clear explanation instead of silently returning an
  empty list that could be mistaken for "analyzed, found nothing." This subsystem needs a
  live Airflow/dbt instance to build and validate against, which isn't available yet.
- `pyairflowtester dependency ...` commands (build/impact/lineage/blast-radius/detect-cycles/
  detect-orphans/risk-score): the command group existed and was tested at the unit level but
  was never actually attached to the main CLI, so none of these commands worked. Wired in,
  plus fixed a JSON-serialization bug in `dependency build --output` (enum dict keys aren't
  JSON-serializable).
- Two test bugs: a pytest test class shadowing the real `TestCoverageAnalyzer` it was
  testing (renamed to `TestTestCoverageAnalyzer`), and an assertion checking for the typo'd
  rule ID `AFG006` instead of `AFW006`.
- `pyproject.toml`'s `testpaths` pointed at the (mostly empty) Rust `tests/` directory
  instead of `python/tests/`, so a bare `pytest` from repo root silently ran almost nothing.

### Changed

- Build backend switched from `maturin` (PyO3/Rust) to `hatchling` (pure Python). The CLI
  never used the Rust extension (`pyairflowtester._core` import already had an `ImportError`
  fallback) so shipping it as a compiled extension added a Rust toolchain requirement for no
  functional benefit. The Rust crate (`src/*.rs`) still exists in the repo as a separate,
  unwired implementation.
- Removed unused runtime dependencies: `sqlalchemy`, `psycopg2-binary`, `pydantic`,
  `jinja2`, `python-dateutil`, `pyyaml`, and all `opentelemetry-*` packages — zero references
  to any of them anywhere in `python/pyairflowtester`. Only `click` and `rich` are actually
  used at runtime.
- README rewritten to describe what actually works today, what's explicitly unimplemented
  (`Analyzer`), and the real architecture (pure-Python CLI is the supported path; the Rust
  core is a separate, unwired experiment).
- `ruff check --fix` applied for import-hygiene/ordering issues.

### Added

- 22 new regression tests locking in the fixes above (circular-dependency graph detection,
  full rule-catalog wiring, per-rule exception isolation, config boolean coercion, positional
  `dag_id` parsing).

## [0.1.0] - 2024-08-02

### Complete System Release

Initial production release of PyAirflowTester with all four integrated phases.

### Added

#### Phase 1: Graph Intelligence (2,340 LOC)
- 12 optimized graph algorithms
  - BFS/DFS traversal (upstream/downstream)
  - Cycle detection via DFS
  - Orphan detection (sources, sinks, isolated)
  - Tarjan's strongly connected components
  - Path finding and reachability analysis
  - Node centrality calculation
  - Critical path analysis
  - Disconnected component detection

- 4 core analysis engines
  - ImpactAnalysisEngine: Downstream impact calculation
  - BlastRadiusEngine: Deployment risk assessment
  - RiskScoringEngine: 0-10 node criticality scoring
  - DriftDetectionEngine: Before/after dependency comparison

- 3 dependency parsers
  - AirflowDAGParser: Python AST-based DAG parsing
  - dbtManifestParser: JSON manifest parsing with lineage
  - AirflowDatasetParser: Dataset connection extraction
  - UnifiedGraphBuilder: Multi-source graph combination

- 7 CLI commands
  - `dependency build`: Construct complete graph
  - `dependency impact`: Analyze node impact
  - `dependency lineage`: View dependency relationships
  - `dependency blast-radius`: Calculate deployment safety
  - `dependency detect-cycles`: Find circular dependencies
  - `dependency detect-orphans`: Identify isolated nodes
  - `dependency risk-score`: Calculate node risk metrics

- 60+ comprehensive tests with 85%+ coverage

#### Phase 2: Analytics & Compliance (1,200 LOC)
- OwnershipAnalyzer: Team and owner impact analysis
- SchemaEvolutionTracker: Data model change tracking
- SLAValidator: SLA compliance monitoring
- TestCoverageAnalyzer: Test adequacy metrics
- 30+ tests validating all scenarios

#### Phase 3: Intelligence & Recommendations (1,100 LOC)
- FailurePredictionEngine: ML-ready failure prediction
- AnomalyDetector: Unusual pattern identification
- RecommendationEngine: Smart improvement suggestions
- HealthScoreCalculator: System health scoring (0-100)
- 20+ tests for all intelligence features

#### Phase 4: Observability & Monitoring (1,300 LOC)
- MetricsCollector: Time-series metrics collection
- AlertManager: Threshold-based alerting system
- EventLogger: Complete audit trail
- DashboardBuilder: System health dashboards
- 25+ tests validating observability features

#### Testing Framework (10,100 LOC)
- 35 static analysis rules for Airflow DAGs
- 15 configuration audit rules
- 3 dbt quality rules
- 67+ test cases with 80%+ coverage
- GitHub Actions CI/CD integration
- Pre-commit hook support

### Features

**Graph Intelligence**
- Support for 14 node types (DAG, task, model, test, dataset, etc.)
- 7 relationship types (depends_on, triggers, dataset_producer, etc.)
- 4 severity levels for risk assessment
- Full ownership and metadata tracking

**Unified Dependency Graph**
- Parse Airflow DAGs via Python AST
- Parse dbt manifests (models, tests, sources, snapshots, exposures)
- Support for Airflow datasets
- External system and API references

**Analysis & Impact**
- Understand downstream impact of any change
- Calculate blast radius before deployment
- Identify critical paths
- Predict deployment safety
- Group impact by severity and type

**Risk & Intelligence**
- 0-10 node risk scoring
- Failure probability prediction
- Anomaly detection (cycles, isolated nodes, high centrality)
- Automated smart recommendations
- System health scoring (0-100)

**Real-Time Monitoring**
- Execution metrics collection
- Threshold-based alerting
- Event audit trail
- System health dashboards

**Production Ready**
- 15,840 lines of production code
- 200+ test cases
- 85%+ code coverage
- Enterprise-grade error handling
- Comprehensive documentation (12,000+ LOC)

### Performance

- Graph construction: 4.2 seconds for 1,000+ DAGs
- Cycle detection: 67ms
- Cached queries: 1.2ms (27x speedup)
- Memory usage: <500MB for 100,000 nodes

### Documentation

- Complete README with problem-first positioning
- 13-part system specification (8,000 LOC)
- 8-part caching strategy guide (3,500 LOC)
- 8 working examples
- Contributing guidelines
- Code of conduct
- GitHub issue and PR templates

### Distribution

- Published to PyPI: https://pypi.org/project/pyairflowtester/
- Published to GitHub: https://github.com/Mullassery/PyAirflowTester/releases/tag/v0.1.0
- Binary wheel for macOS ARM64
- Source distribution (.tar.gz)

## Roadmap

### Phase 5: Advanced Features (Weeks 17-20)
- Real-time streaming integration (Kafka, Pub/Sub)
- ML-based anomaly detection
- Predictive maintenance scheduling
- Cost optimization analysis
- Data quality scoring

### Phase 6: Enterprise Features (Weeks 21-24)
- Multi-tenant support
- Advanced RBAC
- Compliance reporting (SOX, HIPAA, GDPR)
- Advanced visualization (Grafana, Tableau)
- Distributed tracing integration

### Phase 7: Platform Evolution (Weeks 25-28)
- GraphQL API
- Webhook system
- Custom rule engine
- Third-party integrations
- Mobile dashboards

## Contributors

- Georgi Mammen Mullassery (Creator & Lead)
- Community contributors (encouraged to open PRs)

## Support

- Issues: https://github.com/Mullassery/PyAirflowTester/issues
- Discussions: https://github.com/Mullassery/PyAirflowTester/discussions
- Documentation: See README and root .md files

## License

Proprietary. See LICENSE file for details.

---

PyAirflowTester: Enterprise-grade dependency intelligence for modern data platforms.
