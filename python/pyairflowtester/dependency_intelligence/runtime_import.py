"""Sandboxed runtime-import fallback for dynamically-generated DAGs.

`AirflowDAGParser` (parsers.py) is pure AST pattern-matching: it looks for
literal `DAG(...)`/`*Operator(...)` calls and `set_upstream`/`set_downstream`
attribute calls in the source text. DAGs built via factory functions,
dynamic loops, or `exec`/`eval` don't have any of those literal shapes in
their source -- the task graph only exists after the module actually runs.

This module is the fallback for that case: import the DAG file for real, in
an isolated subprocess (so a buggy or malicious DAG file can't corrupt or
hang this process), and read back whatever real `airflow.models.DAG`/task
objects resulted -- which, having actually executed, have their `>>`/
`set_upstream` wiring fully resolved regardless of how dynamically the
tasks were constructed.

Per this project's own design (see README/CLAUDE.md), Airflow is not a hard
runtime dependency -- static analysis works without it installed. This
fallback is opt-in and requires it: if `airflow` isn't importable in the
sandboxed subprocess, `parse_dag_via_runtime_import` reports that plainly
rather than guessing at a dependency graph with no framework to resolve it
against.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Memory ceiling for the sandboxed subprocess. Real Airflow DAG modules doing
# import-time work (reading connections, building large task fan-outs) can
# legitimately need more than a few dozen MB, but this still bounds a runaway
# or hostile DAG file from consuming unbounded memory on the host.
_DEFAULT_MEMORY_LIMIT_BYTES = 512 * 1024 * 1024
_DEFAULT_TIMEOUT_SECONDS = 30.0

_SANDBOX_SCRIPT = r"""
import importlib.util
import json
import sys

try:
    import resource
    _soft, _hard = resource.getrlimit(resource.RLIMIT_AS)
    _limit = {memory_limit_bytes}
    _hard_limit = _hard if _hard != resource.RLIM_INFINITY else _limit
    resource.setrlimit(resource.RLIMIT_AS, (_limit, _hard_limit))
except Exception:
    pass  # RLIMIT_AS isn't available everywhere; degrade to timeout-only sandboxing.

result = {{"dag_id": None, "task_ids": [], "dependencies": [], "error": None}}

try:
    import airflow  # noqa: F401
    from airflow.models import DAG
except ImportError:
    result["error"] = "airflow_not_installed"
    print(json.dumps(result))
    sys.exit(0)

file_path = {file_path!r}

try:
    spec = importlib.util.spec_from_file_location("_pyairflowtester_sandboxed_dag", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
except Exception as exc:
    result["error"] = f"import_failed: {{type(exc).__name__}}: {{exc}}"
    print(json.dumps(result))
    sys.exit(0)

dags = [obj for obj in vars(module).values() if isinstance(obj, DAG)]
if not dags:
    result["error"] = "no_dag_found_after_import"
    print(json.dumps(result))
    sys.exit(0)

dag = dags[0]
result["dag_id"] = dag.dag_id
result["task_ids"] = sorted(dag.task_dict.keys())

dependencies = []
for task_id, task in dag.task_dict.items():
    for upstream_id in sorted(getattr(task, "upstream_task_ids", []) or []):
        dependencies.append([upstream_id, task_id])
result["dependencies"] = dependencies

print(json.dumps(result))
"""


def parse_dag_via_runtime_import(
    file_path: str,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    memory_limit_bytes: int = _DEFAULT_MEMORY_LIMIT_BYTES,
) -> Tuple[Optional[str], List[str], List[Tuple[str, str]]]:
    """Import `file_path` in a sandboxed subprocess and extract the real,
    fully-resolved DAG task graph -- the fallback for DAGs
    `AirflowDAGParser`'s static AST parsing can't see into.

    Returns the same `(dag_id, task_ids, dependencies)` shape as
    `AirflowDAGParser.parse_dag_code`, so this is a drop-in fallback: call
    the static parser first, and only fall back to this (slower, requires
    `airflow` installed, actually executes the file) when it comes back
    empty or incomplete.

    Never raises for expected failure modes (airflow not installed, the
    file failing to import, no DAG object found, timeout) -- returns
    `(None, [], [])` and logs instead, since a fallback that can itself
    crash the caller isn't a usable fallback.
    """
    import logging

    logger = logging.getLogger(__name__)

    resolved_path = str(Path(file_path).resolve())
    script = _SANDBOX_SCRIPT.format(file_path=resolved_path, memory_limit_bytes=memory_limit_bytes)

    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        logger.warning(
            "Runtime-import fallback timed out after %ss parsing %s", timeout_seconds, file_path
        )
        return None, [], []

    if proc.returncode != 0 or not proc.stdout.strip():
        logger.warning(
            "Runtime-import fallback failed for %s (exit %s): %s",
            file_path,
            proc.returncode,
            proc.stderr.strip()[-2000:],
        )
        return None, [], []

    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        logger.warning("Runtime-import fallback produced unparseable output for %s", file_path)
        return None, [], []

    if payload.get("error"):
        logger.info("Runtime-import fallback for %s: %s", file_path, payload["error"])
        return None, [], []

    dependencies = [(pair[0], pair[1]) for pair in payload.get("dependencies", [])]
    return payload.get("dag_id"), list(payload.get("task_ids", [])), dependencies


def parse_dag_file_with_fallback(
    file_path: str,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
) -> Tuple[Optional[str], List[str], List[Tuple[str, str]]]:
    """Parse a DAG file with `AirflowDAGParser` first; if that finds no
    tasks (the signature of a dynamically-generated DAG the static parser
    can't see into), fall back to `parse_dag_via_runtime_import`.

    This is the function most callers want -- it gets the AST parser's
    speed and zero-dependency behavior for the common case, and only pays
    for a sandboxed subprocess import when static analysis genuinely came
    up empty.
    """
    from .parsers import AirflowDAGParser

    dag_id, task_ids, dependencies = AirflowDAGParser.parse_dag_file(file_path)
    if task_ids:
        return dag_id, task_ids, dependencies

    return parse_dag_via_runtime_import(file_path, timeout_seconds=timeout_seconds)
