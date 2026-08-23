"""
DAG analysis rules.
"""

import re
from typing import Any, Dict, List, Set, Tuple


class BaseRule:
    """Base rule class."""

    def __init__(self):
        self.id = ""
        self.name = ""
        self.severity = ""
        self.category = ""
        self.execution_mode = ""

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Evaluate rule against source code."""
        raise NotImplementedError


class CircularDependencyRule(BaseRule):
    """Detect circular dependencies in DAGs."""

    def __init__(self):
        super().__init__()
        self.id = "AFW001"
        self.name = "Circular Dependency"
        self.severity = "critical"
        self.category = "reliability"
        self.execution_mode = "static"

    # Matches chains like "task_a >> task_b >> task_c" (2+ nodes)
    _DOWNSTREAM_CHAIN = re.compile(r"\b\w+(?:\s*>>\s*\w+)+\b")
    # Matches chains like "task_a << task_b << task_c" (2+ nodes)
    _UPSTREAM_CHAIN = re.compile(r"\b\w+(?:\s*<<\s*\w+)+\b")
    _SET_DOWNSTREAM = re.compile(r"(\w+)\.set_downstream\(\s*(\w+)\s*\)")
    _SET_UPSTREAM = re.compile(r"(\w+)\.set_upstream\(\s*(\w+)\s*\)")

    def _extract_edges(self, source_code: str) -> List[Tuple[str, str]]:
        """Extract directed task-dependency edges (upstream -> downstream) from source."""
        edges: List[Tuple[str, str]] = []

        for match in self._DOWNSTREAM_CHAIN.finditer(source_code):
            nodes = re.split(r"\s*>>\s*", match.group())
            edges.extend(zip(nodes, nodes[1:]))

        for match in self._UPSTREAM_CHAIN.finditer(source_code):
            nodes = re.split(r"\s*<<\s*", match.group())
            # "a << b" means b is upstream of a, i.e. edge b -> a
            edges.extend(zip(nodes[1:], nodes))

        for m in self._SET_DOWNSTREAM.finditer(source_code):
            edges.append((m.group(1), m.group(2)))

        for m in self._SET_UPSTREAM.finditer(source_code):
            # "a.set_upstream(b)" means b -> a
            edges.append((m.group(2), m.group(1)))

        return edges

    @staticmethod
    def _has_cycle(edges: List[Tuple[str, str]]) -> bool:
        """Detect a cycle in a directed graph via DFS with coloring."""
        graph: Dict[str, Set[str]] = {}
        for upstream, downstream in edges:
            graph.setdefault(upstream, set()).add(downstream)
            graph.setdefault(downstream, set())

        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in graph}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbor in graph.get(node, ()):
                if color.get(neighbor) == GRAY:
                    return True
                if color.get(neighbor) == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        return any(color[node] == WHITE and dfs(node) for node in list(graph))

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect circular dependencies via graph-cycle detection over parsed edges."""
        violations = []

        edges = self._extract_edges(source_code)
        if edges and self._has_cycle(edges):
            violations.append(
                {
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": file_name,
                    "message": "Circular dependency detected in task graph",
                    "remediation": "Review task dependencies and remove cycles",
                }
            )

        return violations


class MissingSLARule(BaseRule):
    """Detect missing SLAs on production DAGs."""

    def __init__(self):
        super().__init__()
        self.id = "AFW002"
        self.name = "Missing SLA"
        self.severity = "high"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect missing SLAs."""
        violations = []

        # Check if DAG has SLA defined
        if "sla" not in source_code.lower() and "production" in file_name.lower():
            violations.append(
                {
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": file_name,
                    "message": "Production DAG missing SLA configuration",
                    "remediation": "Add 'sla' parameter to DAG definition",
                }
            )

        return violations


class ExpensiveImportsRule(BaseRule):
    """Detect expensive imports in DAG files."""

    def __init__(self):
        super().__init__()
        self.id = "AFW003"
        self.name = "Expensive Imports"
        self.severity = "medium"
        self.category = "performance"
        self.execution_mode = "static"
        self.expensive_modules = ["tensorflow", "torch", "sklearn", "pandas", "numpy"]

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect expensive imports."""
        violations = []

        for module in self.expensive_modules:
            pattern = rf"^import\s+{module}|^from\s+{module}\s+import"
            if re.search(pattern, source_code, re.MULTILINE):
                violations.append(
                    {
                        "rule_id": self.id,
                        "severity": self.severity,
                        "affected_resource": module,
                        "message": f"Expensive import detected: {module}",
                        "remediation": f"Move '{module}' import inside task or use lazy import",
                    }
                )

        return violations


class ParseTimeRule(BaseRule):
    """Analyze DAG parse time."""

    def __init__(self):
        super().__init__()
        self.id = "AFW004"
        self.name = "Parse Time Analysis"
        self.severity = "medium"
        self.category = "performance"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Analyze parse time."""
        violations = []

        # Check for potentially slow patterns
        if re.search(r"for\s+\w+\s+in\s+.*:\s+create.*DAG", source_code, re.DOTALL):
            violations.append(
                {
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": file_name,
                    "message": "DAG file contains loop-based DAG generation (slow parsing)",
                    "remediation": "Use task factories or DAG generation patterns",
                }
            )

        return violations
