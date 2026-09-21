# ROADMAP_HONEST

Honest status tracking for PyAirflowTester, in four buckets. Written/updated 2026-09-19
during an OSS-standardization pass that included running the real test/lint/type-check
suite, starting `pyairflowtester serve` and hitting its routes, running `actionlint` and
`pip-audit`/`cargo audit` for real, and reading the actual source for every claim below —
not carried forward from old docs without verification. See README.md for the user-facing
version of "what works today."

## 1. Built and tested (verified working)

- `pyairflowtester scan/rules/score` and `dependency build/impact/lineage/blast-radius/
  detect-cycles/detect-orphans/risk-score` — 205 tests pass (`pip install -e ".[dev,web]"`;
  198 pass / 1 skipped without the `web` extra), verified by running `pytest python/tests/
  -v` myself on Python 3.11.16, and by running `pyairflowtester scan`/`rules` against
  `examples/` directly.
- `pyairflowtester serve` — started it for real (`pyairflowtester serve --dags examples/
  --port 8099`), confirmed `GET /` and `GET /health` both return HTTP 200 with real rendered
  HTML (not JSON), graph built with 7 nodes from `examples/`.
- `ruff check python/` and `black --check python/` — both clean, verified 2026-09-19.
- `FailurePredictionEngine`/`HealthScoreCalculator` test-coverage wiring — **this pass found
  the README's prior claim that these hardcode `test_count=0`/a fixed `10.0` was wrong and
  out of date.** Reading `dependency_intelligence/intelligence.py` directly confirms both
  call the real `TestCoverageAnalyzer`, and `test_test_score_varies_with_real_coverage_data`
  in `python/tests/test_dependency_intelligence_phase2.py` asserts real variance. README.md
  has been corrected. The one real remaining simplification: the historical-failure-rate
  factor still assumes a fixed 30-day window (`intelligence.py`, `days_of_data = 30`) instead
  of computing it from real event timestamps.
- `pip-audit` against the full `[dev,web]` dependency set — "No known vulnerabilities found"
  (verified 2026-09-19; re-run yourself, this drifts).
- `.github/dependabot.yml` (added this pass) — weekly update PRs for `pip`, `cargo`, and
  `github-actions` ecosystems.
- `.github/workflows/ci.yml`'s new `pip-audit` job (added this pass) — runs the same
  `pip-audit` command for real in CI, not `continue-on-error`.

## 2. Built but not tested / thin coverage (works in the paths that are tested; unverified elsewhere)

- **`cli.py` and `dependency_intelligence/cli.py`: 0% test coverage.** These are the actual
  `click` command wiring that every `pyairflowtester ...` invocation goes through. Every
  underlying class is well-tested, but a broken option name, wrong argument passthrough, or
  exit-code bug in the CLI layer itself would not be caught by the test suite. Manually
  running a handful of commands (`scan`, `rules`, `serve`) during this pass worked, but that
  is not the same as coverage. **Worth a dedicated follow-up**: add `CliRunner`-based tests
  (click provides one) for each subcommand's argument parsing and exit codes.
- **`report.py`: 20% coverage** (`python/pyairflowtester/report.py:31-216` mostly
  uncovered) — HTML/SARIF/JSON report rendering is exercised only incidentally.
- **`rules/dbt.py`: 22% coverage** (lines 36-77, 93-128, 144-194 uncovered) — the three dbt
  manifest rules (DBT001-DBT003) have much thinner direct test coverage than the AFW/CFG
  rule families.
- **`scanner.py`: 66% coverage**, **`analyzer.py`: 56%** (the unimplemented-stub paths,
  expected), **`observability.py`: 84%**, **`parsers.py`: 72%**.
- Rust crate (`src/*.rs`): `cargo clippy -- -D warnings` passes cleanly (verified). `cargo
  test`/`cargo build --release` were **not** verified to pass — see bucket 3, this is a real
  build/link failure, not just "untested."

## 3. CI / build errors, actually broken (verified, not assumed)

- **`cargo test` / `cargo build --release` fail to link on macOS arm64** — reproduced
  directly during this pass:
  ```
  ld: symbol(s) not found for architecture arm64
  Undefined symbols: _Py_InitializeEx, _PyUnicode_..., _PyType_..., etc.
  ```
  Root cause: `Cargo.toml:15` sets `pyo3 = { version = "0.20", features =
  ["extension-module"] }`. That feature deliberately omits linking against `libpython`
  (correct for building a `cdylib` that Python `dlopen`s and resolves symbols for at
  runtime) — but it also breaks `cargo test`/plain `cargo build` for the same crate, which
  need to link a standalone binary. `cargo clippy`/`cargo check` are unaffected (they stop
  before linking), which is why `make lint` and the CI `rust-tests` job's clippy step work.
  Whether `.github/workflows/ci.yml`'s `rust-tests` job (`cargo test --verbose` +
  `cargo build --release`, run on `ubuntu-latest`) actually passes in CI is **unverified** —
  Linux's lazy ELF symbol resolution can mask this at link time in ways macOS's linker
  doesn't, so it may well pass there while being broken for any contributor on macOS. This
  environment's sandboxed network couldn't reach `api.github.com` to check actual recent run
  history (PyPI and readthedocs.io were reachable; `gh run list` timed out). **This needs a
  dedicated follow-up**: either feature-gate `extension-module` behind a non-default Cargo
  feature so `cargo test` works out of the box, or explicitly document that Rust-side testing
  requires `maturin develop`-style invocation instead of bare `cargo test`.
- ~~**mypy: 36 real type errors, invisible in CI.**~~ **Fixed 2026-09-21.** All 36 errors
  triaged and resolved (`mypy python/pyairflowtester --ignore-missing-imports` is clean); the
  `|| true` in `ci.yml`'s mypy step has been removed, so mypy now actually gates CI. Notable
  fixes:
  - `dependency_intelligence/graph.py:329` (`get_critical_path`'s inner `dfs`) — was
    annotated to return `List[str]` but never returned a value (mutated a `nonlocal` instead)
    and its return value was never used by any caller; retyped to `-> None` to match actual
    behavior, no logic change.
  - `dependency_intelligence/graph.py:219` (`detect_cycles`) — cache round-trips through
    `Optional[Any]`; added an explicit `cast(List[List[str]], cached)` rather than silently
    returning `Any`.
  - `dependency_intelligence/observability.py:152` (`AlertManager.thresholds`) — this **was**
    a real bug in the type annotation (not the runtime logic): declared
    `Dict[str, Dict[str, float]]` but `set_threshold` actually stores a nested
    `{"warning": float, "critical": float}` dict per metric type, and `check_threshold`
    already correctly indexed it that way (`thresholds["critical"]`). Corrected the
    annotation to `Dict[str, Dict[str, Dict[str, float]]]` to match the real structure — no
    behavior change, the runtime code was already right, only the type was lying.
  - `dependency_intelligence/cli.py:50,117,164,207,250,293,332` and `web/app.py:303` (8 call
    sites) — fixed by correcting `UnifiedGraphBuilder.build_unified_graph`'s signature
    (`dependency_intelligence/parsers.py:355-359`) from `dag_files: List[str] = None` /
    `dbt_manifest: str = None` / `dataset_files: List[str] = None` (all implicitly-Optional,
    the actual source of the mismatch) to properly `Optional[...]`-typed parameters.
  - `dependency_intelligence/analytics.py:253` (`SLAValidator.validate_node`) — `sla_target`
    is `Optional[str]` from a `.get()`, but is only passed to `_is_compliant` (which requires
    `str`) in the branch where `has_sla` is already known `True`; mypy can't see that
    correlation, so added an explicit `sla_target is not None` guard (behavior-preserving,
    since `has_sla` already guarantees it).
  - `dependency_intelligence/parsers.py` — `AirflowDAGParser`/`AirflowDatasetParser` read
    `ast.Constant.value`, typed by typeshed as a broad literal union, and stored it directly
    into `dag_id`/`task_ids`/`datasets` without normalizing to `str`; added explicit `str(...)`
    conversions at each site (`dag_id`, `task_id`, dataset `uri`) plus a `unique_id`/`name`
    default of `""` in the unused `parse_model_node` helper (only caller is
    `src/dbt_parser.rs`'s independent Rust implementation, so no live Python code path was
    affected either way).
  - Remaining ~20 errors were `var-annotated`/`no_implicit_optional` (missing type
    annotations, implicit-Optional defaults) across `rules/dbt.py`, `scanner.py`, `models.py`,
    `analytics.py`, `graph.py` — mechanical annotation fixes, no behavior change.
  Verified: `mypy python/pyairflowtester --ignore-missing-imports` clean, `ruff check
  python/` clean, `black --check python/` clean, full `pytest python/tests/` still 205
  passed (no regressions from the annotation/typing changes).
- **`cargo audit` finds real advisories** (already surfaced by a prior session, still
  unresolved as of this pass, confirmed still present): sqlx 0.7.4 (RUSTSEC-2024-0363, needs
  >=0.8.1) and a rustls-related advisory (RUSTSEC-2026-0098), plus 2 unmaintained-crate
  warnings. `continue-on-error: true` in `ci.yml`, so visible but non-blocking. Doesn't affect
  the shipped Python package (Rust crate isn't built into it), but is a real, unresolved item
  for the Rust crate's own dependency tree.
- **`codecov/codecov-action@v4` (bumped from the actionlint-flagged `v3` this pass) requires
  a `CODECOV_TOKEN` secret even for public repos as of v4** — whether that secret is
  configured on this GitHub repo was **not verified** (no `gh`/API access in this sandbox to
  check repo secrets, and secrets can't be listed by value anyway). Added
  `continue-on-error: true` to that step so a missing token doesn't fail the whole
  `python-tests` job; if the token isn't set, coverage upload will silently no-op — check the
  Codecov project dashboard to confirm uploads are actually landing.
- **`integration-tests` job**: guarded (`if [ -d "python/tests/integration" ]`), and that
  directory doesn't exist — this Postgres-backed integration suite was never written. Not a
  bug (already honestly guarded by a prior session), just confirming it's still true.
- **`deploy-docs` job**: guarded (`if [ -f "docs/Makefile" ] && [ -f "docs/conf.py" ]`), and
  neither file exists — no Sphinx site was ever built. Confirmed still true. The
  `pyproject.toml` `Documentation` URL (`https://pyairflowtester.readthedocs.io`) was a dead
  link (verified: HTTP 404) and has been removed as part of this pass.
- Outdated GitHub Actions versions flagged by `actionlint` and fixed this pass:
  `actions/cache@v3`→`v4`, `actions/setup-python@v4`→`v5` (4 occurrences),
  `codecov/codecov-action@v3`→`v4`, `peaceiris/actions-gh-pages@v3`→`v4`. `actionlint
  .github/workflows/ci.yml` is clean after these changes (verified).

## 4. Not built (no hedging — these don't exist)

- **Runtime correlation (`Analyzer` class / `pyairflowtester connect`).** Every method raises
  `AnalyzerNotImplementedError` (`python/pyairflowtester/analyzer.py`) by design — not a fake
  stub, a deliberate fail-fast. Needs a live Airflow metadata DB + dbt run history to build
  and validate against, which isn't available in this project's current development setup.
- **Real-time streaming (Kafka/Pub/Sub) integration.** Does not exist anywhere in the
  codebase — confirmed by `grep -ri kafka\|pubsub` returning nothing outside historical/
  archived docs and the now-removed speculative CHANGELOG "Phase 5" entry. Not on any current
  concrete plan; would need a real message-queue-backed use case to justify the added
  dependency weight (this package is deliberately `click`+`rich`-only at runtime).
- **L2 (Redis) and L4 (DuckDB) cache tiers.** `dependency_intelligence/cache.py` has real L1
  (in-memory) and L3 (SQLite) tiers; L2/L4 were designed on paper (see
  `docs/archive/DEPENDENCY_CACHING_STRATEGY.md`, historical) but never implemented.
- **Sphinx documentation site.** No `docs/conf.py`, no `docs/Makefile`, no
  `.readthedocs.yaml` anywhere in the repo. The `deploy-docs` CI job and the
  `pyproject.toml` `Documentation` URL both referenced this; the CI job is guarded to no-op,
  and the dead URL has been removed (see bucket 3).
- **Postgres-backed integration test suite.** `python/tests/integration/` does not exist.
  The `integration-tests` CI job stands up a real Postgres service container and then no-ops
  because there's nothing to run against it.
- **Rust core wired into the CLI.** `src/*.rs` (PyO3 bindings) is a separate, independent
  reimplementation of some rule/parsing/scoring logic. `pyairflowtester/__init__.py` imports
  it opportunistically and falls back to `None`; nothing in the CLI calls into it even when
  built. This is a real architectural fork that needs a decision (reconcile the two
  implementations and wire it in for real, or drop the Rust crate) — not something to leave
  ambiguous indefinitely, per the README's own roadmap.
- **GDPR/HIPAA/SOX/CCPA "compliance features", RBAC "support", "SLA enforcement"** as
  previously described in SECURITY.md — these were fabricated/mislabeled claims removed
  during this pass (see SECURITY.md's "What is NOT true, corrected here" section for the
  specifics). The tool has *rules that check* whether your own Airflow config enables
  RBAC/TLS/encryption, and it *validates* SLAs you define against data you feed it — it does
  not implement any of those things itself.

## Not attempted in this pass, and why

- **`docs/architecture/README.md` with Mermaid diagrams** — not added. The existing prose
  "Architecture" section in README.md (two independent things: Python CLI vs. unwired Rust
  crate) is a two-paragraph explanation; a diagram wouldn't add information a paragraph
  doesn't already convey, and none of the actual runtime data flows (graph construction →
  analysis engines → optional web rendering) are complex enough to need one yet. Revisit if
  the dependency-intelligence engine count grows.
- **Reorganizing `python/` into a `src/` layout** — not done. `python/pyairflowtester/` +
  `python/tests/` is already an intentional, working layout (not clutter); moving it would be
  churn with no functional benefit.
- **Converting `.github/ISSUE_TEMPLATE/*.md` to YAML forms** — not done; the existing
  Markdown templates are present and reasonably structured, not missing, so this wasn't a
  "genuinely appropriate" change to force through in a documentation-focused pass.
- **Fixing the PyO3 linker issue** — deliberately left as a documented finding (bucket 3),
  not fixed: it needs a Cargo feature-gating decision (or a documented `maturin develop`-only
  testing workflow) that isn't a drive-by quick fix. (The 36 mypy errors, by contrast, were
  triaged and fixed in a later quick-fix pass on 2026-09-21 — see bucket 3's mypy entry.)
