# Competitive intelligence in roadmap and upgrade work

**Policy date:** 2026-10-19

Competitive findings are an input to product decisions, not a one-off report.
Every pending roadmap item, new feature, and routine dependency upgrade should
check the repository's [`AUDIT_FINDINGS.md`](AUDIT_FINDINGS.md) before work
starts, and record the decision in the PR or changelog.

## Required check before building

1. **Read `AUDIT_FINDINGS.md`.** Find the relevant competitor row and the
   ranked next actions. If the finding is stale, update it with a dated source.
2. **Name the competitor and the user problem.** A feature is not justified by
   "competitor has it". State the workflow it unlocks, who needs it, and how
   often. Mark unverified demand as a hypothesis.
3. **Prefer reuse over new code.** Check whether an existing Mullassery repo
   already provides the capability (see `BUNDLES.md` in the profile repo and
   the bundle role file in this repo, when present). Typical reuse:
   - crawling/fetching/robots/SSRF → **MudFish**
   - architecture maps / PR diffs → **CodeAtlas**
   - data-quality contracts / validation → **StatGuardian**
   - token counting / cost tables → **PyTokenCalc**
   - dependency graph / advisories / SBOM → **PyDeepMesh**
   - segmentation / CLV / churn → **ClusterAudienceKit**
   - activation / lineage / PII → **PyReverseETL**
   - fleet state sync → **SyncFleet** (only after conflict resolution)
4. **Choose one disposition:** build, integrate, defer, or reject. Write it
   down. A rejection with a reason is a successful outcome.
5. **For routine upgrades**, check whether the upgrade closes a known
   competitor gap or breaks a differentiated capability. Run the tests that
   cover the affected path; do not merge a green build that silently changes a
   user-visible contract.

## PR / changelog checklist

- [ ] Competitor and source URL/date recorded (or "no direct competitor").
- [ ] User impact and frequency stated; unverified demand labelled.
- [ ] Reuse check done against sibling repos/bundles.
- [ ] Failure mode and rollback considered (especially auth, PII, cost).
- [ ] Docs/roadmap status updated honestly.
- [ ] Tests or a manual verification command included.

## Review cadence

- Refresh the competitor row when a release changes the capability.
- Re-check the full `AUDIT_FINDINGS.md` at least quarterly and before a major
  release.
- If a finding is wrong or stale, correct it in the same PR that relies on it.

## Non-goals

- Copying features for parity.
- Adding a dependency just because a competitor uses it.
- Treating star counts or download counts as proof of user need.

## OSS gap analysis — 2026-10-24

**What matters most here:** runtime correlation and a CI gate. The analyzer raises `NotImplementedError` and `scan` always exits 0, so the tool cannot yet prove a DAG is safe or fail a pipeline. Finish the analyzer and add `--fail-on`.

Scope: open-source tools that validate Airflow DAGs, dbt artifacts, or the
Airflow/dbt boundary before deployment; runtime products are included where
they overlap run-history work. Dates and licenses verified 2026-10-24.

### Comparable OSS projects

- **Apache Airflow** — `https://github.com/apache/airflow`; Apache-2.0; v3.3.2
  (2026-09-17). DagBag import validation, `dag.test`, and configuration checks;
  no lint catalog, risk score, or cross-tool blast radius.
- **Elementary** — `https://github.com/elementary-data/elementary`;
  Apache-2.0; v0.26.1 (2026-10-11). dbt-native test results, alerts, lineage,
  and report UI; no Airflow DAG analysis.
- **Astronomer Cosmos** — `https://github.com/astronomer/astronomer-cosmos`;
  Apache-2.0; v1.16.0a3 (2026-10-23; pre-release), v1.15.1 stable (2026-08-04).
  Renders/runs dbt as Airflow tasks and parses the manifest; no static Airflow
  lint or risk score.
- **dbt-checkpoint** — `https://github.com/dbt-checkpoint/dbt-checkpoint`;
  MIT; v2.0.10 (2026-06-18). Pre-commit hooks for dbt files and manifest
  metadata; no Airflow coverage.

### Capability comparison

| Capability | PyAirflowTester | Apache Airflow | Elementary | Cosmos | dbt-checkpoint |
| --- | --- | --- | --- | --- | --- |
| Static Airflow DAG analysis (AST) | Yes | Partial | No | No | No |
| Static dbt manifest analysis | Yes | No | Partial | Yes | Yes |
| Unified Airflow + dbt graph | Yes | No | No | Partial | No |
| Rule breadth incl. airflow.cfg | Yes | Partial | No | No | Partial |
| Blast radius / impact | Yes | No | Partial | Partial | No |
| Risk scoring | Yes | No | No | No | No |
| Runtime run-history correlation | No | Yes | Yes | Yes | No |
| Executes dbt tests or SQL | No | Partial | Yes | Yes | No |
| SARIF/HTML/JSON reports | Yes | No | Partial | No | No |
| Web UI | Partial | Yes | Yes | Partial | No |
| CI/pre-commit gate | No | No | Partial | No | Yes |

### Gaps that matter (ranked)

1. **Runtime correlation is stubbed.** `Analyzer` raises
   `AnalyzerNotImplementedError` for every run-history method
   (`python/pyairflowtester/analyzer.py`); competitors reason over real runs.
   Effort: L. Build; this is the largest credibility gap.
2. **No CI failure gate.** `scan` always exits 0 and only writes SARIF/HTML
   when `--output` is supplied; there is no `--fail-on`, so CI cannot fail a PR.
   Effort: S. Build first; it is cheap and unlocks adoption.
3. **No real-DAG validation corpus.** There are 235 Python tests and 35 Rust
   tests, but no production-DAG corpus or false-positive study. Airflow 3 parser
   coverage is asserted, not evidenced. Effort: M. Build a fixture corpus and
   compare against DagBag import results.
4. **`scan .` does not auto-discover inputs.** Without `--dags`, `--dbt`, and
   `--airflow-cfg`, the path produces no analysis. Effort: S. Build discovery
   with explicit overrides.
5. **Risk scoring is unvalidated.** The score is a weighted severity formula
   with no calibration and no explanation of which weights drive a critical
   result. Effort: M. Build calibration and a transparent breakdown.
6. **No dbt execution.** Elementary and Cosmos run dbt and expose real test
   results. Effort: L. Defer or reject; integrate rather than reimplement.
7. **Distribution and docs gaps.** Alpha, no GitHub release, a 404 docs URL,
   and PyPI license metadata of `None` weaken trust. Effort: S. Fix before
   adding features.

### Where we are differentiated

- Static analysis without an Airflow runtime, covering DAG code, dbt metadata, and `airflow.cfg` in one scan.
- A unified graph connecting Airflow dependencies to dbt lineage for cross-tool blast radius.
- Risk scoring and SARIF/HTML/JSON output aimed at pre-merge review.
- OpenLineage ingestion into local SQLite; complements DagBag rather than replacing runtime checks.

### Disposition

**Build.** P1 is CI gating, runtime correlation, and evidence from real Airflow
3.x DAGs; P2 is auto-discovery and score calibration. Defer the UI and reject a
dbt runner. Do not claim production readiness until a real-DAG corpus and a
non-zero CI gate exist.

### Sources

- https://github.com/apache/airflow/releases/tag/3.3.2
- https://raw.githubusercontent.com/apache/airflow/main/LICENSE
- https://github.com/elementary-data/elementary/releases/tag/v0.26.1
- https://raw.githubusercontent.com/elementary-data/elementary/master/LICENSE
- https://github.com/astronomer/astronomer-cosmos/releases/tag/astronomer-cosmos-v1.16.0a3
- https://raw.githubusercontent.com/astronomer/astronomer-cosmos/main/LICENSE
- https://github.com/dbt-checkpoint/dbt-checkpoint/releases/tag/v2.0.10
- https://pypi.org/project/pyairflowtester/0.5.4/
- Repository evidence: `README.md`, `AUDIT_FINDINGS.md`, `ROADMAP_HONEST.md`, `analyzer.py`, `cli.py`.
