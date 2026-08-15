"""
Advanced DAG analysis rules (AFW005-AFW015).

These rules detect more subtle anti-patterns and configuration issues.
"""

import re
from typing import Any, Dict, List


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


class TaskCountRule(BaseRule):
    """Detect DAGs with excessive task counts."""

    def __init__(self):
        super().__init__()
        self.id = "AFW005"
        self.name = "Excessive Task Count"
        self.severity = "medium"
        self.category = "performance"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect DAGs with >500 tasks."""
        violations = []

        # Count task definitions
        task_patterns = [
            r"@task\(",
            r"@task_group\(",
            r"PythonOperator\(",
            r"BashOperator\(",
            r"SqlOperator\(",
        ]

        task_count = sum(len(re.findall(pattern, source_code)) for pattern in task_patterns)

        if task_count > 500:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": file_name,
                "message": f"DAG has {task_count} tasks (exceeds 500 limit)",
                "remediation": "Split into multiple DAGs or use SubDAGs/task groups",
            })

        return violations


class CatchupConfigRule(BaseRule):
    """Detect problematic catchup configurations."""

    def __init__(self):
        super().__init__()
        self.id = "AFW006"
        self.name = "Risky Catchup Configuration"
        self.severity = "high"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect catchup=True without backfill strategy."""
        violations = []

        if re.search(r"catchup\s*=\s*True", source_code):
            if not re.search(r"backfill|batch_run", source_code):
                violations.append({
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": file_name,
                    "message": "catchup=True enabled without backfill strategy",
                    "remediation": "Add backfill logic or set catchup=False for production",
                })

        return violations


class SourceCodePoolConfigurationRule(BaseRule):
    """Detect default pool usage in DAG source code (AFW007)."""

    def __init__(self):
        super().__init__()
        self.id = "AFW007"
        self.name = "Default Pool Usage"
        self.severity = "medium"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect tasks using default pool (128 slot limit)."""
        violations = []

        # Count tasks with explicit pool vs. without
        task_with_pool = len(re.findall(r"pool\s*=\s*['\"]", source_code))
        all_tasks = len(re.findall(r"Operator\(", source_code))

        if task_with_pool == 0 and all_tasks > 0:
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": file_name,
                "message": "Tasks using default pool (limited to 128 slots)",
                "remediation": "Create dedicated pool for this DAG or set explicit pool",
            })

        return violations


class HardcodedConnectionRule(BaseRule):
    """Detect hardcoded connection IDs."""

    def __init__(self):
        super().__init__()
        self.id = "AFW008"
        self.name = "Hardcoded Connection ID"
        self.severity = "high"
        self.category = "maintainability"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect hardcoded connection strings."""
        violations = []

        # Look for common hardcoded patterns
        patterns = [
            r"conn_id\s*=\s*['\"].*@.*['\"]",  # User@host pattern
            r"connection_string\s*=\s*['\"].*://.*['\"]",  # URL pattern
            r"host\s*=\s*['\"]localhost['\"]",
        ]

        for pattern in patterns:
            if re.search(pattern, source_code):
                violations.append({
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": file_name,
                    "message": "Hardcoded connection ID or host detected",
                    "remediation": "Use environment variables or Airflow variables",
                })
                break

        return violations


class SecretsInCodeRule(BaseRule):
    """Detect secrets in DAG code."""

    def __init__(self):
        super().__init__()
        self.id = "AFW009"
        self.name = "Secrets in Code"
        self.severity = "critical"
        self.category = "security"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect hardcoded secrets."""
        violations = []

        secret_patterns = [
            (r"password\s*=\s*['\"][^'\"]+['\"]", "password"),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "api_key"),
            (r"token\s*=\s*['\"][^'\"]+['\"]", "token"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "secret"),
        ]

        for pattern, secret_type in secret_patterns:
            if re.search(pattern, source_code):
                violations.append({
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": file_name,
                    "message": f"Hardcoded {secret_type} detected in source code",
                    "remediation": "Move to environment variables, AWS Secrets Manager, or Airflow Variables",
                })
                break

        return violations


class RetryConfigurationRule(BaseRule):
    """Detect problematic retry configurations."""

    def __init__(self):
        super().__init__()
        self.id = "AFW010"
        self.name = "Excessive Retries"
        self.severity = "medium"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect retries > 5 without backoff."""
        violations = []

        # Find retry counts
        retry_matches = re.findall(r"retries\s*=\s*(\d+)", source_code)

        for retry_count in retry_matches:
            if int(retry_count) > 5:
                if "exponential_backoff" not in source_code and "retry_delay" not in source_code:
                    violations.append({
                        "rule_id": self.id,
                        "severity": self.severity,
                        "affected_resource": file_name,
                        "message": f"High retry count ({retry_count}) without backoff strategy",
                        "remediation": "Add exponential_backoff or configure retry_delay",
                    })
                    break

        return violations


class SensorTimeoutRule(BaseRule):
    """Detect sensors with problematic timeout settings."""

    def __init__(self):
        super().__init__()
        self.id = "AFW011"
        self.name = "Sensor Timeout Risk"
        self.severity = "medium"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect sensors with >1h timeout."""
        violations = []

        if "Sensor" in source_code or "sensor" in source_code:
            timeout_matches = re.findall(r"timeout\s*=\s*(\d+)", source_code)

            for timeout_val in timeout_matches:
                if int(timeout_val) > 3600:  # 1 hour in seconds
                    violations.append({
                        "rule_id": self.id,
                        "severity": self.severity,
                        "affected_resource": file_name,
                        "message": f"Sensor timeout > 1 hour ({timeout_val}s) without exponential backoff",
                        "remediation": "Use exponential_backoff and poke_interval for sensors",
                    })
                    break

        return violations


class BranchComplexityRule(BaseRule):
    """Detect complex branching logic."""

    def __init__(self):
        super().__init__()
        self.id = "AFW012"
        self.name = "Complex Branching"
        self.severity = "low"
        self.category = "maintainability"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect BranchPythonOperator with complex logic."""
        violations = []

        if "BranchPythonOperator" in source_code:
            # Count lines in python_callable to estimate complexity
            branch_blocks = re.findall(r"def\s+\w+\(.*?\):(.+?)(?=\n(?:def|class|\Z))", source_code, re.DOTALL)

            for block in branch_blocks:
                line_count = block.count("\n")
                if line_count > 30:
                    violations.append({
                        "rule_id": self.id,
                        "severity": self.severity,
                        "affected_resource": file_name,
                        "message": "BranchPythonOperator has complex logic (>30 lines)",
                        "remediation": "Simplify branching logic or split into separate operations",
                    })
                    break

        return violations


class DocumentationRule(BaseRule):
    """Detect missing DAG documentation."""

    def __init__(self):
        super().__init__()
        self.id = "AFW013"
        self.name = "Missing Documentation"
        self.severity = "low"
        self.category = "maintainability"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect DAGs without description."""
        violations = []

        if not re.search(r"description\s*=\s*['\"]", source_code):
            violations.append({
                "rule_id": self.id,
                "severity": self.severity,
                "affected_resource": file_name,
                "message": "DAG missing description",
                "remediation": "Add description parameter to DAG definition",
            })

        return violations


class AlertingConfigurationRule(BaseRule):
    """Detect missing alerting."""

    def __init__(self):
        super().__init__()
        self.id = "AFW014"
        self.name = "No Alerting Configured"
        self.severity = "medium"
        self.category = "reliability"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect production DAGs without alerts."""
        violations = []

        if "production" in file_name.lower() or "prod" in file_name.lower():
            if not re.search(r"on_failure_callback|on_retry_callback|email", source_code):
                violations.append({
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": file_name,
                    "message": "Production DAG has no failure alerting configured",
                    "remediation": "Add on_failure_callback, on_retry_callback, or email notifications",
                })

        return violations


class OperatorDeprecationRule(BaseRule):
    """Detect deprecated operators."""

    def __init__(self):
        super().__init__()
        self.id = "AFW015"
        self.name = "Deprecated Operator"
        self.severity = "medium"
        self.category = "maintainability"
        self.execution_mode = "static"

    def evaluate(self, source_code: str, file_name: str = "") -> List[Dict[str, Any]]:
        """Detect deprecated Airflow operators."""
        violations = []

        deprecated = {
            "SubDagOperator": "Use task groups instead (@task_group)",
            "DummyOperator": "Use EmptyOperator instead",
            "BranchPythonOperator": "Consider using TaskFlow API",
        }

        for operator, recommendation in deprecated.items():
            if operator in source_code:
                violations.append({
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": operator,
                    "message": f"Deprecated operator used: {operator}",
                    "remediation": recommendation,
                })
                break

        return violations
