"""
dbt analysis rules.
"""

from typing import List, Dict, Any
import json


class BaseRule:
    """Base rule class."""

    def __init__(self):
        self.id = ""
        self.name = ""
        self.severity = ""
        self.category = ""
        self.execution_mode = ""

    def evaluate(self, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate rule against manifest."""
        raise NotImplementedError


class MissingTestsRule(BaseRule):
    """Detect models without tests."""

    def __init__(self):
        super().__init__()
        self.id = "DBT001"
        self.name = "Missing Tests"
        self.severity = "high"
        self.category = "data_quality"
        self.execution_mode = "static"

    def evaluate(self, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect models without tests."""
        violations = []

        # Extract models
        models = {}
        if "nodes" in manifest:
            for key, node in manifest["nodes"].items():
                if key.startswith("model."):
                    model_name = node.get("name", "")
                    models[model_name] = node

        # Check which models have tests
        tested_models = set()
        if "nodes" in manifest:
            for key, node in manifest["nodes"].items():
                if key.startswith("test."):
                    # Find which model this test belongs to
                    if "attached_node" in node:
                        tested_models.add(node["attached_node"])
                    elif "depends_on" in node and "nodes" in node["depends_on"]:
                        for dep in node["depends_on"]["nodes"]:
                            if dep.startswith("model."):
                                tested_models.add(dep)

        # Find untested models (excluding ephemeral and temp)
        for model_name, model in models.items():
            materialization = model.get("config", {}).get("materialized", "table")
            is_public = model.get("config", {}).get("meta", {}).get("public", True)

            if is_public and materialization not in ["ephemeral", "temporary"]:
                model_key = f"model.{model.get('package_name', '')}.{model_name}"
                if model_key not in tested_models:
                    violations.append({
                        "rule_id": self.id,
                        "severity": self.severity,
                        "affected_resource": model_name,
                        "message": f"Model '{model_name}' has no tests",
                        "remediation": "Add tests for this model in schema.yml",
                    })

        return violations


class RedundantTestsRule(BaseRule):
    """Detect redundant test definitions."""

    def __init__(self):
        super().__init__()
        self.id = "DBT002"
        self.name = "Redundant Tests"
        self.severity = "low"
        self.category = "maintainability"
        self.execution_mode = "static"

    def evaluate(self, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect redundant tests."""
        violations = []

        # Track test signatures (model + test_type + column)
        test_signatures = {}

        if "nodes" in manifest:
            for key, node in manifest["nodes"].items():
                if key.startswith("test."):
                    test_name = node.get("name", "")
                    test_type = node.get("test_metadata", {}).get("name", "")

                    # Build signature
                    if "attached_node" in node:
                        signature = f"{node['attached_node']}:{test_type}"
                    else:
                        signature = f"{test_name}:{test_type}"

                    if signature not in test_signatures:
                        test_signatures[signature] = []

                    test_signatures[signature].append(test_name)

        # Find duplicates
        for signature, test_list in test_signatures.items():
            if len(test_list) > 1:
                violations.append({
                    "rule_id": self.id,
                    "severity": self.severity,
                    "affected_resource": signature,
                    "message": f"Redundant tests found: {', '.join(test_list[:2])}...",
                    "remediation": "Consolidate duplicate tests",
                })

        return violations


class UntestedModelRule(BaseRule):
    """Detect untested public models."""

    def __init__(self):
        super().__init__()
        self.id = "DBT003"
        self.name = "Untested Public Model"
        self.severity = "medium"
        self.category = "data_quality"
        self.execution_mode = "static"

    def evaluate(self, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect untested public models."""
        violations = []

        # Find high-importance models with no tests
        if "nodes" in manifest:
            for key, node in manifest["nodes"].items():
                if key.startswith("model."):
                    model_name = node.get("name", "")
                    description = node.get("description", "")
                    test_count = len(node.get("test_dependencies", []))

                    # Check if model is marked as critical
                    is_critical = (
                        "critical" in description.lower() or
                        test_count == 0 and len(node.get("columns", {})) > 5
                    )

                    if is_critical and test_count == 0:
                        violations.append({
                            "rule_id": self.id,
                            "severity": self.severity,
                            "affected_resource": model_name,
                            "message": f"Critical model '{model_name}' has no tests",
                            "remediation": "Add comprehensive tests for this critical model",
                        })

        return violations
