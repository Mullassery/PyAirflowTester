"""
Static AST parser for Airflow DAG metadata.

This is the Python counterpart of the (unshipped) Rust ``DagParser`` in
``src/dag_parser.rs``. It parses a DAG module with :mod:`ast` -- never by
importing it -- and fills every field of :class:`pyairflowtester.models.DagDefinition`,
including the three metadata fields the Rust parser computed but Python did not:

* ``max_task_depth`` -- number of tasks in the longest dependency chain.
* ``dynamic_dag_detected`` -- whether tasks/DAGs are generated dynamically.
* ``external_dependencies`` -- external systems referenced by operator classes,
  ``conn_id`` values, SQL strings, or module imports.

Dependencies are read from ``>>``/``<<`` expressions (including list operands
such as ``[a, b] >> c``) and from ``task.set_upstream(...)`` /
``task.set_downstream(...)`` calls, matching the Rust implementation.
"""

import ast
import logging
import re
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

from pyairflowtester.models import DagDefinition

logger = logging.getLogger(__name__)

_EXPENSIVE_MODULES = ("tensorflow", "torch", "sklearn", "pandas", "numpy")

# Canonical order and markers mirror ``DagParser::detect_external_dependencies``
# in ``src/dag_parser.rs``. Matching is done against operator/module names,
# ``conn_id``/SQL string literals, and imported modules rather than raw source
# text, so comments and unrelated identifiers cannot trigger a false positive.
_EXTERNAL_PATTERNS: Tuple[Tuple[str, Tuple[re.Pattern[str], ...]], ...] = (
    (
        "S3",
        (
            re.compile(r"s3://", re.IGNORECASE),
            re.compile(r"(?<![a-z0-9])s3(?![a-z0-9])", re.IGNORECASE),
            re.compile(r"s3[a-z_]*(?:operator|hook|conn)", re.IGNORECASE),
        ),
    ),
    (
        "BigQuery",
        (
            re.compile(r"bigquery", re.IGNORECASE),
            re.compile(r"(?<![a-z0-9])bq(?![a-z0-9])", re.IGNORECASE),
        ),
    ),
    ("Snowflake", (re.compile(r"snowflake", re.IGNORECASE),)),
    ("PostgreSQL", (re.compile(r"postgres(?:ql)?|psycopg", re.IGNORECASE),)),
    ("MySQL", (re.compile(r"mysql", re.IGNORECASE),)),
    ("Redshift", (re.compile(r"redshift", re.IGNORECASE),)),
    (
        "API",
        (
            re.compile(r"https?://", re.IGNORECASE),
            re.compile(r"(?<![a-z0-9])requests(?![a-z0-9])", re.IGNORECASE),
            re.compile(r"(?<![a-z0-9])httpx(?![a-z0-9])", re.IGNORECASE),
            re.compile(r"(?<![a-z0-9])urllib", re.IGNORECASE),
            re.compile(r"(?<![a-z0-9])http(?![a-z0-9])", re.IGNORECASE),
            re.compile(r"http[a-z_]*(?:operator|hook|sensor)", re.IGNORECASE),
        ),
    ),
)


def _string_value(node: ast.AST) -> Optional[str]:
    """Return a string literal's value, or ``None`` for non-literals."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _dotted_name(node: ast.AST) -> Optional[str]:
    """Return ``module.Class.method`` for a Name/Attribute expression."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _call_short_name(node: ast.AST) -> Optional[str]:
    """Return the final component of a call target (``S3CreateObjectOperator``)."""
    name = _dotted_name(node)
    return name.rsplit(".", 1)[-1] if name else None


def _keyword_string(call: ast.Call, keyword_name: str) -> Optional[str]:
    for keyword in call.keywords:
        if keyword.arg == keyword_name:
            return _string_value(keyword.value)
    return None


def _iter_calls(tree: ast.AST) -> Iterable[ast.Call]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            yield node


def _iter_assigned_calls(tree: ast.AST) -> Iterable[Tuple[str, ast.Call]]:
    """Yield ``(variable_name, call)`` for assignments of call results."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not isinstance(node.value, ast.Call):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    yield target.id, node.value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and isinstance(node.value, ast.Call):
                yield node.target.id, node.value
        elif isinstance(node, ast.NamedExpr):
            if isinstance(node.target, ast.Name) and isinstance(node.value, ast.Call):
                yield node.target.id, node.value


def _decorator_names(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef],
) -> List[str]:
    names = []
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        name = _call_short_name(target)
        if name:
            names.append(name)
    return names


def _extract_task_ids(tree: ast.AST) -> Dict[str, str]:
    """Map task identity -> declared ``task_id``.

    Operator-style tasks use their ``task_id`` keyword. TaskFlow tasks use
    their function name unless the ``@task`` decorator overrides ``task_id``.
    """
    task_ids: Dict[str, str] = {}

    for call in _iter_calls(tree):
        task_id = _keyword_string(call, "task_id")
        if task_id:
            task_ids[task_id] = task_id

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if "task" not in _decorator_names(node):
            continue
        declared = node.name
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and _call_short_name(decorator.func) == "task":
                declared = _keyword_string(decorator, "task_id") or node.name
                break
        task_ids[node.name] = declared
        task_ids.setdefault(declared, declared)

    return task_ids


def _extract_var_to_task(tree: ast.AST, task_ids: Dict[str, str]) -> Dict[str, str]:
    """Map local variable names / TaskFlow function names to task identities."""
    mapping: Dict[str, str] = {}

    for variable, call in _iter_assigned_calls(tree):
        short_name = _call_short_name(call.func)
        if not short_name or not short_name.endswith("Operator"):
            continue
        declared = _keyword_string(call, "task_id")
        if declared:
            mapping[variable] = declared

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if "task" in _decorator_names(node) and node.name in task_ids:
                mapping[node.name] = task_ids[node.name]

    return mapping


def _task_names(
    node: ast.AST,
    var_to_task: Dict[str, str],
) -> List[str]:
    """Resolve one side of a dependency expression to task identities."""
    if isinstance(node, ast.Name):
        return [var_to_task.get(node.id, node.id)]
    if isinstance(node, ast.Attribute):
        name = node.attr
        return [var_to_task.get(name, name)]
    if isinstance(node, ast.Call):
        return _task_names(node.func, var_to_task)
    if isinstance(node, ast.BinOp):
        return _task_names(node.left, var_to_task) + _task_names(node.right, var_to_task)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        names: List[str] = []
        for element in node.elts:
            names.extend(_task_names(element, var_to_task))
        return names
    return []


def _flatten_chain(node: ast.AST, operator_type: type) -> List[ast.AST]:
    """Flatten a left-associative ``>>``/``<<`` chain into its operands."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, operator_type):
        return _flatten_chain(node.left, operator_type) + _flatten_chain(node.right, operator_type)
    return [node]


def _build_dependency_graph(
    tree: ast.AST,
    task_ids: Dict[str, str],
) -> Tuple[Set[str], Dict[str, List[str]], List[Tuple[str, str]]]:
    """Build nodes/adjacency/edge list from shifts and ``set_upstream`` calls."""
    var_to_task = _extract_var_to_task(tree, task_ids)
    nodes: Set[str] = set(task_ids.values())
    adjacency: Dict[str, List[str]] = {}
    ordered_edges: List[Tuple[str, str]] = []
    seen_edges: Set[Tuple[str, str]] = set()

    def add_edge(upstream: str, downstream: str) -> None:
        if not upstream or not downstream:
            return
        nodes.add(upstream)
        nodes.add(downstream)
        if (upstream, downstream) in seen_edges:
            return
        seen_edges.add((upstream, downstream))
        ordered_edges.append((upstream, downstream))
        adjacency.setdefault(upstream, []).append(downstream)

    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.RShift, ast.LShift)):
            operands = _flatten_chain(node, type(node.op))
            groups = [_task_names(operand, var_to_task) for operand in operands]
            for index in range(len(groups) - 1):
                left, right = groups[index], groups[index + 1]
                if isinstance(node.op, ast.RShift):
                    for upstream in left:
                        for downstream in right:
                            add_edge(upstream, downstream)
                else:
                    # ``a << b`` means b is upstream of a.
                    for upstream in right:
                        for downstream in left:
                            add_edge(upstream, downstream)

        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in ("set_upstream", "set_downstream"):
            continue

        targets = _task_names(node.func.value, var_to_task)
        arguments: List[str] = []
        for argument_node in node.args:
            arguments.extend(_task_names(argument_node, var_to_task))

        for target in targets:
            for argument_name in arguments:
                if node.func.attr == "set_upstream":
                    add_edge(argument_name, target)
                else:
                    add_edge(target, argument_name)

    return nodes, adjacency, ordered_edges


def _calculate_max_depth(nodes: Set[str], adjacency: Dict[str, List[str]]) -> int:
    """Return the number of tasks in the longest dependency chain."""
    if not nodes:
        return 0

    memo: Dict[str, int] = {}
    visiting: Set[str] = set()

    def longest_chain(node: str) -> int:
        if node in memo:
            return memo[node]
        if node in visiting:
            return 0
        visiting.add(node)
        best = 1
        for successor in adjacency.get(node, ()):
            best = max(best, 1 + longest_chain(successor))
        visiting.remove(node)
        memo[node] = best
        return best

    return max(longest_chain(node) for node in nodes)


def _has_cycle(nodes: Set[str], adjacency: Dict[str, List[str]]) -> bool:
    visited: Set[str] = set()
    visiting: Set[str] = set()

    def visit(node: str) -> bool:
        if node in visited:
            return False
        if node in visiting:
            return True
        visiting.add(node)
        for successor in adjacency.get(node, ()):
            if visit(successor):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in nodes)


def _detect_dynamic_dag(tree: ast.AST) -> bool:
    """Detect loops, ``globals()``, task groups, and dynamic task mapping."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            return True
        if isinstance(node, ast.Call):
            name = _call_short_name(node.func)
            if name in ("globals", "expand"):
                return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if "task_group" in _decorator_names(node):
                return True
    return False


def _detect_expensive_imports(tree: ast.AST) -> List[str]:
    """Return expensive third-party modules imported by the DAG module."""
    imported: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    found = []
    for module in _EXPENSIVE_MODULES:
        if any(name == module or name.startswith(f"{module}.") for name in imported):
            found.append(module)
    return found


def _docstring_node_ids(tree: ast.AST) -> Set[int]:
    docstrings: Set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and _string_value(node.body[0].value) is not None
            ):
                docstrings.add(id(node.body[0].value))
    return docstrings


def _collect_external_tokens(tree: ast.AST) -> List[str]:
    """Collect operator/module names and non-docstring string literals."""
    docstrings = _docstring_node_ids(tree)
    tokens: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _dotted_name(node.func)
            if name:
                tokens.append(name)
                tokens.append(name.rsplit(".", 1)[-1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                tokens.append(alias.name)
                tokens.append(alias.asname or alias.name.rsplit(".", 1)[-1])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                tokens.append(node.module)
            for alias in node.names:
                tokens.append(alias.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstrings:
                tokens.append(node.value)

    return tokens


def _detect_external_dependencies(tree: ast.AST) -> List[str]:
    """Return external systems referenced by operators, conn ids, SQL, or imports."""
    tokens = _collect_external_tokens(tree)
    found = []
    for system, patterns in _EXTERNAL_PATTERNS:
        if any(pattern.search(token) for token in tokens for pattern in patterns):
            found.append(system)
    return found


def _extract_dag_id(tree: ast.AST) -> Optional[str]:
    """Extract the DAG id from ``DAG(...)``, ``@dag(...)``, or ``dag_id = ...``."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "dag_id":
                    value = _string_value(node.value)
                    if value:
                        return value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "dag_id":
                value = _string_value(node.value) if node.value is not None else None
                if value:
                    return value
        elif isinstance(node, ast.Call):
            short_name = _call_short_name(node.func)
            if short_name not in ("DAG", "dag"):
                continue
            if node.args:
                value = _string_value(node.args[0])
                if value:
                    return value
            value = _keyword_string(node, "dag_id")
            if value:
                return value

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if "dag" in _decorator_names(node):
                return node.name

    return None


def _count_tasks(tree: ast.AST, task_ids: Dict[str, str]) -> int:
    return len({task_ids[name] for name in task_ids})


class DagParser:
    """Parse Airflow DAG files into :class:`DagDefinition` metadata."""

    def parse_code(self, source_code: str, file_path: str = "<string>") -> DagDefinition:
        """Parse DAG source code without importing or executing it."""
        started = time.perf_counter()
        tree = ast.parse(source_code, filename=file_path)

        task_ids = _extract_task_ids(tree)
        nodes, adjacency, _ = _build_dependency_graph(tree, task_ids)
        dag_id = _extract_dag_id(tree) or Path(file_path).stem or "unknown"

        return DagDefinition(
            dag_id=dag_id,
            file_path=file_path,
            source_code=source_code,
            parse_time_ms=(time.perf_counter() - started) * 1000.0,
            task_count=_count_tasks(tree, task_ids),
            task_ids=sorted({task_ids[name] for name in task_ids}),
            max_task_depth=_calculate_max_depth(nodes, adjacency),
            has_cycles=_has_cycle(nodes, adjacency),
            dynamic_dag_detected=_detect_dynamic_dag(tree),
            expensive_imports=_detect_expensive_imports(tree),
            external_dependencies=_detect_external_dependencies(tree),
        )

    def parse_file(self, file_path: Union[str, Path]) -> DagDefinition:
        """Read and parse one DAG file."""
        path = Path(file_path)
        started = time.perf_counter()
        source_code = path.read_text(encoding="utf-8")
        dag = self.parse_code(source_code, file_path=str(path))
        dag.parse_time_ms = (time.perf_counter() - started) * 1000.0
        return dag

    def parse_directory(self, directory: Union[str, Path]) -> List[DagDefinition]:
        """Parse every non-private ``*.py`` file in a directory."""
        dags = []
        for path in sorted(Path(directory).glob("*.py")):
            if path.name.startswith("_"):
                continue
            try:
                dags.append(self.parse_file(path))
            except (OSError, SyntaxError) as exc:
                logger.warning("Skipping unparseable DAG file %s: %s", path, exc)
        return dags


def parse_dag_code(source_code: str, file_path: str = "<string>") -> DagDefinition:
    """Convenience wrapper around :meth:`DagParser.parse_code`."""
    return DagParser().parse_code(source_code, file_path=file_path)


def parse_dag_file(file_path: Union[str, Path]) -> DagDefinition:
    """Convenience wrapper around :meth:`DagParser.parse_file`."""
    return DagParser().parse_file(file_path)


def parse_dag_directory(directory: Union[str, Path]) -> List[DagDefinition]:
    """Convenience wrapper around :meth:`DagParser.parse_directory`."""
    return DagParser().parse_directory(directory)
