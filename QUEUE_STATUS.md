# Queue status — 2026-10-20

This file records what was shipped, what is blocked/failed, and what is rejected for this repository. It complements `AUDIT_FINDINGS.md`.

## Shipped
- OpenLineage runtime lineage ingestion and SQLGlot column-level SQL lineage (`pyairflowtester openlineage` / `columns`).

## Blocked / failed
- Runtime correlation via Airflow REST/dbt run_results.

## Rejected / deferred
- A test runner.
- Shipping or exposing the Rust crate in `src/*.rs`. Audited 2026-10-20: it duplicates
  Python parsing/scoring, implements no production rules, and exposes stubs; see README
  "Rust crate status".

## Policy

Any future feature or upgrade must check `AUDIT_FINDINGS.md` and this file before implementation. A blocked item is retried only when its external dependency is available; a rejected item needs new user evidence or a design change to reopen.
