"""
Scanner module for artifact analysis.

Performs static analysis on Airflow DAGs and dbt projects to detect
violations before deployment.
"""

from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Scanner:
    """Static analysis scanner for artifacts."""

    def __init__(self):
        """Initialize scanner."""
        self.dag_rules = self._get_dag_rules()
        self.dbt_rules = self._get_dbt_rules()

    def scan_dags(self, dags_path: Path) -> List[Dict[str, Any]]:
        """
        Scan Airflow DAGs directory.

        Args:
            dags_path: Path to DAGs directory

        Returns:
            List of violations found
        """
        violations = []
        logger.info(f"Scanning DAGs in {dags_path}")

        for dag_file in dags_path.glob("*.py"):
            if dag_file.name.startswith("_"):
                continue

            try:
                with open(dag_file) as f:
                    source_code = f.read()

                # Apply DAG rules
                for rule in self.dag_rules:
                    rule_violations = rule.evaluate(source_code, dag_file.name)
                    violations.extend(rule_violations)

            except Exception as e:
                logger.error(f"Error scanning {dag_file}: {e}")

        logger.info(f"Found {len(violations)} DAG violations")
        return violations

    def scan_dbt(self, dbt_path: Path) -> List[Dict[str, Any]]:
        """
        Scan dbt project.

        Args:
            dbt_path: Path to dbt project

        Returns:
            List of violations found
        """
        violations = []
        logger.info(f"Scanning dbt project in {dbt_path}")

        # Look for manifest.json
        manifest_path = dbt_path / "target" / "manifest.json"
        if not manifest_path.exists():
            logger.warning(f"manifest.json not found in {dbt_path / 'target'}")
            return violations

        try:
            import json
            with open(manifest_path) as f:
                manifest = json.load(f)

            # Apply dbt rules
            for rule in self.dbt_rules:
                rule_violations = rule.evaluate(manifest)
                violations.extend(rule_violations)

        except Exception as e:
            logger.error(f"Error scanning dbt project: {e}")

        logger.info(f"Found {len(violations)} dbt violations")
        return violations

    def _get_dag_rules(self) -> List:
        """Get DAG analysis rules."""
        from pyairflowtester.rules.dag import (
            CircularDependencyRule,
            MissingSLARule,
            ExpensiveImportsRule,
            ParseTimeRule,
        )

        return [
            CircularDependencyRule(),
            MissingSLARule(),
            ExpensiveImportsRule(),
            ParseTimeRule(),
        ]

    def _get_dbt_rules(self) -> List:
        """Get dbt analysis rules."""
        from pyairflowtester.rules.dbt import (
            MissingTestsRule,
            RedundantTestsRule,
            UntestedModelRule,
        )

        return [
            MissingTestsRule(),
            RedundantTestsRule(),
            UntestedModelRule(),
        ]

    def _get_scorer(self):
        """Get scorer instance."""
        from pyairflowtester.scoring import Scorer
        return Scorer()
