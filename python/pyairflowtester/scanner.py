"""
Scanner module for artifact analysis.

Performs static analysis on Airflow DAGs and dbt projects to detect
violations before deployment.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class Scanner:
    """Static analysis scanner for artifacts."""

    def __init__(self):
        """Initialize scanner."""
        self.dag_rules = self._get_dag_rules()
        self.dbt_rules = self._get_dbt_rules()
        self.config_rules = self._get_config_rules()

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
            except Exception as e:
                logger.error(f"Error reading {dag_file}: {e}")
                continue

            # Apply DAG rules. Each rule is isolated: a rule raising an
            # exception must not suppress findings from the other rules
            # for this file.
            for rule in self.dag_rules:
                try:
                    rule_violations = rule.evaluate(source_code, dag_file.name)
                    violations.extend(rule_violations)
                except Exception as e:
                    logger.warning(
                        f"Rule {getattr(rule, 'id', rule.__class__.__name__)} "
                        f"failed on {dag_file.name}: {e}"
                    )

        logger.info(f"Found {len(violations)} DAG violations")
        return violations

    def scan_config(self, config_path: Path) -> List[Dict[str, Any]]:
        """
        Scan an airflow.cfg configuration file.

        Args:
            config_path: Path to an airflow.cfg (INI-format) file

        Returns:
            List of violations found
        """
        violations = []
        logger.info(f"Scanning Airflow configuration at {config_path}")

        try:
            config = self._parse_airflow_cfg(config_path)
        except Exception as e:
            logger.error(f"Error reading {config_path}: {e}")
            return violations

        # Apply config rules. Each rule is isolated so one failing rule
        # does not suppress findings from the others.
        for rule in self.config_rules:
            try:
                rule_violations = rule.evaluate(config)
                violations.extend(rule_violations)
            except Exception as e:
                logger.warning(
                    f"Rule {getattr(rule, 'id', rule.__class__.__name__)} "
                    f"failed on {config_path}: {e}"
                )

        logger.info(f"Found {len(violations)} configuration violations")
        return violations

    @staticmethod
    def _parse_airflow_cfg(config_path: Path) -> Dict[str, Dict[str, Any]]:
        """Parse an INI-format airflow.cfg into a nested section -> key -> value dict.

        configparser yields every value as a raw string. Config rules such
        as TLSConfigurationRule/RBACConfigurationRule do truthiness checks
        (`if not enable_ssl`) that need real booleans -- the string "False"
        is truthy in Python, so without coercion those rules would silently
        never fire against a real airflow.cfg. Values are coerced using the
        same boolean vocabulary as configparser.ConfigParser.getboolean
        (1/yes/true/on -> True, 0/no/false/off -> False); everything else
        is left as a string so rules that expect ints/strings (and call
        int(...) themselves) keep working unchanged.
        """
        import configparser

        parser = configparser.ConfigParser()
        parser.read(config_path)

        return {
            section: {
                key: Scanner._coerce_config_value(value) for key, value in parser.items(section)
            }
            for section in parser.sections()
        }

    @staticmethod
    def _coerce_config_value(value: str) -> Any:
        """Coerce an INI string value to bool where it unambiguously looks boolean."""
        lowered = value.strip().lower()
        if lowered in ("1", "yes", "true", "on"):
            return True
        if lowered in ("0", "no", "false", "off"):
            return False
        return value

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
        except Exception as e:
            logger.error(f"Error reading manifest for {dbt_path}: {e}")
            return violations

        # Apply dbt rules. Each rule is isolated so one failing rule does
        # not suppress findings from the others.
        for rule in self.dbt_rules:
            try:
                rule_violations = rule.evaluate(manifest)
                violations.extend(rule_violations)
            except Exception as e:
                logger.warning(
                    f"Rule {getattr(rule, 'id', rule.__class__.__name__)} "
                    f"failed on dbt manifest: {e}"
                )

        logger.info(f"Found {len(violations)} dbt violations")
        return violations

    def _get_dag_rules(self) -> List:
        """Get DAG analysis rules (AFW001-AFW015)."""
        from pyairflowtester.rules.dag import (
            CircularDependencyRule,
            ExpensiveImportsRule,
            MissingSLARule,
            ParseTimeRule,
        )
        from pyairflowtester.rules.dag_advanced import (
            AlertingConfigurationRule,
            BranchComplexityRule,
            CatchupConfigRule,
            DocumentationRule,
            HardcodedConnectionRule,
            OperatorDeprecationRule,
            RetryConfigurationRule,
            SecretsInCodeRule,
            SensorTimeoutRule,
            SourceCodePoolConfigurationRule,
            TaskCountRule,
        )

        return [
            # Basic rules (AFW001-AFW004)
            CircularDependencyRule(),
            MissingSLARule(),
            ExpensiveImportsRule(),
            ParseTimeRule(),
            # Advanced rules (AFW005-AFW015)
            TaskCountRule(),
            CatchupConfigRule(),
            SourceCodePoolConfigurationRule(),
            HardcodedConnectionRule(),
            SecretsInCodeRule(),
            RetryConfigurationRule(),
            SensorTimeoutRule(),
            BranchComplexityRule(),
            DocumentationRule(),
            AlertingConfigurationRule(),
            OperatorDeprecationRule(),
        ]

    def _get_dbt_rules(self) -> List:
        """Get dbt analysis rules (DBT001-DBT003)."""
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

    def _get_config_rules(self) -> List:
        """Get Airflow configuration audit rules (CFG001-CFG015)."""
        from pyairflowtester.rules.config import (
            AirflowCfgPoolConfigurationRule,
            ConcurrencyConfigurationRule,
            DAGFolderConfigurationRule,
            DatabaseBackupRule,
            EncryptionConfigurationRule,
            ExecutorConfigurationRule,
            LogRetentionRule,
            LogStorageRule,
            MaxActiveRunsRule,
            QueueConfigurationRule,
            RBACConfigurationRule,
            SchedulerConfigurationRule,
            TLSConfigurationRule,
            WorkerConfigurationRule,
            XComConfigurationRule,
        )

        return [
            ExecutorConfigurationRule(),
            AirflowCfgPoolConfigurationRule(),
            ConcurrencyConfigurationRule(),
            QueueConfigurationRule(),
            MaxActiveRunsRule(),
            XComConfigurationRule(),
            LogRetentionRule(),
            EncryptionConfigurationRule(),
            TLSConfigurationRule(),
            RBACConfigurationRule(),
            SchedulerConfigurationRule(),
            WorkerConfigurationRule(),
            LogStorageRule(),
            DatabaseBackupRule(),
            DAGFolderConfigurationRule(),
        ]

    def _get_scorer(self):
        """Get scorer instance."""
        from pyairflowtester.scoring import Scorer

        return Scorer()
