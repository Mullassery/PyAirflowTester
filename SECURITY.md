# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please report it responsibly.

**Do not open public GitHub issues for security vulnerabilities.**

Instead, please email: mullassery@gmail.com with:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if available)

This is a small, part-time-maintained open-source project (see README.md "Status") — there is
no dedicated security team and no SLA on response time. Best effort only.

## What this tool actually does, security-wise

PyAirflowTester is a **static analyzer**: it reads Airflow DAG source files, dbt
`manifest.json` files, and `airflow.cfg` files that you point it at, and reports findings. It
does not open network connections, does not execute the DAG/dbt code it scans, and does not
phone home or collect telemetry — verify this yourself, the runtime dependency list is just
`click` and `rich` (see `pyproject.toml`; `fastapi`/`uvicorn`/`jinja2` are added only if you
install the optional `[web]` extra for `pyairflowtester serve`, which binds a local HTTP
server on the port you give it, with no auth — see "Known gaps" below).

Security-relevant rules it runs against the code you point it at (not against this tool
itself):

- `SecretsInCodeRule` (AFW008 — see `python/pyairflowtester/rules/dag_advanced.py`): flags
  hardcoded secrets/credentials in DAG source.
- `RBACConfigurationRule`, TLS/encryption rules, and other `CFG*` rules (see
  `python/pyairflowtester/rules/config.py`): flag *your* `airflow.cfg` if RBAC/TLS/encryption
  are disabled. **These check your Airflow config; this tool does not itself implement RBAC,
  encryption, or access control.**

## Known gaps (read before relying on this for a security posture)

- **`pyairflowtester serve` has no authentication.** It's a local dev-facing dashboard
  (Jinja2-rendered HTML over plain HTTP, no TLS, no login). Do not expose it on an untrusted
  network without putting your own auth/reverse-proxy in front of it.
- **No sandboxing beyond the one place that needs it.** `dependency_intelligence/
  runtime_import.py`'s runtime-import fallback actually imports a DAG file to resolve
  dynamically-built task graphs; it runs in a resource-limited subprocess, but "resource
  limits" is not the same as a real sandbox — don't run it against untrusted DAG files.
- **`cargo audit` (see `.github/workflows/ci.yml`, `security-scan` job) currently finds real
  advisories** in the (unused-by-the-shipped-package) Rust crate's dependency tree: sqlx 0.7.4
  (RUSTSEC-2024-0363, needs >=0.8.1) and a rustls-related advisory (RUSTSEC-2026-0098), plus 2
  unmaintained-crate warnings. The job is `continue-on-error: true` so it's visible without
  blocking merges. Since the Rust crate is not built or shipped as part of the published
  Python package (see README "Architecture"), this does not affect `pip install
  pyairflowtester` users, but it is a real, unresolved item for anyone who does `maturin
  develop`/build it.
- **`pip-audit` (new as of this pass, see `ci.yml`) found no known vulnerabilities** in the
  Python runtime + dev + web dependency set as of 2026-09-19 — re-run it yourself
  (`pip-audit`) since this drifts as new CVEs are published.
- **mypy's 36 current type errors are not enforced** — the CI step runs `mypy ...  || true`,
  so it never fails the build. See ROADMAP_HONEST.md for the count and file locations.

## What is NOT true, corrected here (2026-09-19)

Earlier versions of this file made claims that don't hold up against the actual code and are
removed rather than repeated:

- "Comprehensive test coverage (85%+)" — actual is ~71-74% (see README "Status"), and two
  entire modules (`cli.py`, `dependency_intelligence/cli.py`) have 0% coverage.
- A "Third-Party Security" list naming Pydantic, SQLAlchemy, and OpenTelemetry — none of
  these are dependencies of this project. They were removed as unused in v0.3.0 (see
  CHANGELOG.md) and this file was never updated to match.
- Claims of "GDPR compliance features", "HIPAA-ready", "SOX compliance support", and "CCPA
  support" — this tool has no data-retention, deletion, or encryption features of its own; it
  only *flags* whether your Airflow config enables encryption/RBAC. Presenting a static
  analyzer's config-audit rules as regulatory compliance features was misleading.
- "Support for RBAC" under an "Access Control" heading, implying this tool implements
  access control — it doesn't. It has a rule that checks whether *your* Airflow instance has
  RBAC enabled.
- "SLA enforcement" — `SLAValidator` (see `dependency_intelligence/analyzers.py`) *validates*
  SLAs you define against a graph you build; it does not enforce anything (no alerting
  side-effects, no automatic remediation).

## Supported Versions

- Python 3.10, 3.11, 3.12 (CI matrix; see `.github/workflows/ci.yml`)
- Airflow 2.0+ (only used to shape the DAG source patterns the rules look for — Airflow
  itself is not a runtime dependency)
- dbt: only a `manifest.json` file is needed — dbt itself is not a runtime dependency

## Dependency Management

- `.github/dependabot.yml` (added 2026-09-19) opens weekly PRs for outdated `pip`, `cargo`,
  and GitHub Actions dependencies.
- `ci.yml` runs `pip-audit` (Python) and `cargo audit` (Rust) — see "Known gaps" above for
  current results.

## Contact

For security matters: mullassery@gmail.com
