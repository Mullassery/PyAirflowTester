# Audit findings — 2026-10-19

This file records the repository-specific findings from the portfolio audit
conducted on 2026-10-19. It is documentation only; no code or release artifacts
were changed in this pass unless explicitly noted under "Implementation status".

Sources: the repository's own README/source/workflows, GitHub metadata and
Actions runs, PyPI metadata, and official competitor documentation. Claims are
marked as verified, inferred, or open questions. "Absent" means not found in the
inspected repository/docs, not proof that it cannot exist.

## What it is

Static analysis and dependency intelligence for Airflow DAGs and dbt projects: rules, graph, risk scoring, blast radius, SARIF, and a dashboard.

## Verified strengths

- 33 rules; unified Airflow DAG + dbt manifest graph; impact/blast radius; risk score; JSON/HTML/SARIF; FastAPI dashboard; library API; 40 test files.
- Useful cross-tool static view.

## Verified gaps and user-facing risks

- Runtime correlation is explicitly stubbed (`AnalyzerNotImplementedError`).
- Rust crate exists but is not wired into the CLI and deliberately not shipped (it duplicates Python, contains stubs, and does not build/test cleanly on macOS arm64); pure-Python package. See README "Rust crate status".
- Alpha; no large real-DAG corpus validation; no GitHub release.

## Direct competitors

- Airflow DAG validation, dbt tests, Elementary, Monte Carlo, Dagster.

## Ranked next actions

- P1: finish runtime correlation via Airflow REST/dbt `run_results` (L).
- P2: publish a GitHub Action/example workflow (S).

## Do not build

- A test runner; it analyzes structure, it does not execute DAGs.

## Evidence gaps / validation needed

- No false-positive analysis on real DAGs; no runtime-correlation evidence.

## Recommended disposition

Maintain/finish only if runtime correlation is implemented; otherwise freeze.

## Implementation status

No code changes in this pass.
