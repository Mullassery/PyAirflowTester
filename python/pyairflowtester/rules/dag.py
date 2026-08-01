"""
DAG analysis rules.
"""

from typing import List, Dict, Any
import re


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

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect circular dependencies."""
        violations = []

        # Simple heuristic: look for patterns that might indicate cycles
        patterns = [
            r"\w+\s*>>\s*\w+.*\w+\s*>>\s*\w+.*\w+\s*>>\s*\1",  # A >> B >> C >> A
            r"set_upstream.*set_upstream",
        ]

        for pattern in patterns:
            if re.search(pattern, source_code, re.DOTALL):
                violations.append({
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": file_name,
                    "message": "Potential circular dependency detected",
                    "remediation": "Review task dependencies and remove cycles",
                })
                break

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
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": file_name,
                "message": "Production DAG missing SLA configuration",
                "remediation": "Add 'sla' parameter to DAG definition",
            })

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
                violations.append({
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": module,
                    "message": f"Expensive import detected: {module}",
                    "remediation": f"Move '{module}' import inside task or use lazy import",
                })

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
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": file_name,
                "message": "DAG file contains loop-based DAG generation (slow parsing)",
                "remediation": "Use task factories or DAG generation patterns",
            })

        return violations
