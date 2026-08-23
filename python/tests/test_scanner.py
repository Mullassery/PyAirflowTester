"""Tests for scanner module."""

import logging

import pytest
from pyairflowtester.scanner import Scanner


class TestScanner:
    """Scanner test suite."""

    @pytest.fixture
    def scanner(self):
        """Create scanner instance."""
        return Scanner()

    def test_scanner_initialization(self, scanner):
        """Test scanner initialization."""
        assert scanner is not None
        assert len(scanner.dag_rules) > 0
        assert len(scanner.dbt_rules) > 0
        assert len(scanner.config_rules) > 0

    def test_all_dag_rules_wired(self, scanner):
        """Regression test: scan must run the full DAG rule catalog (AFW001-AFW015),
        not just the 4 basic rules from dag.py. Previously advanced rules like
        SecretsInCodeRule and HardcodedConnectionRule were defined but never
        wired into Scanner._get_dag_rules()."""
        rule_ids = {rule.id for rule in scanner.dag_rules}
        expected_ids = {f"AFW{i:03d}" for i in range(1, 16)}
        assert rule_ids == expected_ids

    def test_all_config_rules_wired(self, scanner):
        """Regression test: config.py's CFG001-CFG015 rules must be wired in
        (previously there was no config-scanning path in Scanner at all)."""
        rule_ids = {rule.id for rule in scanner.config_rules}
        expected_ids = {f"CFG{i:03d}" for i in range(1, 16)}
        assert rule_ids == expected_ids

    def test_secrets_rule_fires_via_scan_dags(self, scanner, tmp_path):
        """End-to-end: SecretsInCodeRule (AFW009) must actually fire through
        Scanner.scan_dags, confirming it is really wired into the scan path
        the CLI uses (not just importable)."""
        dag_file = tmp_path / "prod_pipeline.py"
        dag_file.write_text("password = 'hunter2'\n" "conn_id = 'user@prod-host'\n")

        violations = scanner.scan_dags(tmp_path)

        rule_ids = {v["rule_id"] for v in violations}
        assert "AFW009" in rule_ids  # SecretsInCodeRule
        assert "AFW008" in rule_ids  # HardcodedConnectionRule

    def test_one_bad_rule_does_not_suppress_others(self, scanner, tmp_path, monkeypatch, caplog):
        """Regression test: a single rule raising must not zero out findings
        from the other rules for the same file (the original bug wrapped the
        entire per-file rule loop in one try/except)."""

        def _boom(self, source_code, file_name=""):
            raise ValueError("simulated rule failure")

        # Break exactly one rule; every other rule should still report.
        monkeypatch.setattr(type(scanner.dag_rules[0]), "evaluate", _boom)

        dag_file = tmp_path / "prod.py"
        dag_file.write_text("password = 'hunter2'\n")

        with caplog.at_level(logging.WARNING):
            violations = scanner.scan_dags(tmp_path)

        assert any(v["rule_id"] == "AFW009" for v in violations)
        assert any("simulated rule failure" in r.message for r in caplog.records)

    def test_scan_dag_with_circular_dependency(self, scanner):
        """Test circular dependency detection."""
        source_code = """
from airflow import DAG
task1 >> task2 >> task3 >> task1
"""
        violations = [
            v for rule in scanner.dag_rules for v in rule.evaluate(source_code, "test.py")
        ]
        # Should detect circular dependency
        assert any(v.get("rule_id") == "AFW001" for v in violations)

    def test_scan_dag_missing_sla(self, scanner):
        """Test missing SLA detection."""
        source_code = """
from airflow import DAG
dag = DAG('production_dag', catchup=False)
"""
        violations = [
            v
            for rule in scanner.dag_rules
            for v in rule.evaluate(source_code, "production_test.py")
        ]
        # Should detect missing SLA on production DAG
        assert any(v.get("rule_id") == "AFW002" for v in violations)

    def test_scan_dag_expensive_imports(self, scanner):
        """Test expensive imports detection."""
        source_code = """
import tensorflow as tf
from airflow import DAG
"""
        violations = [
            v for rule in scanner.dag_rules for v in rule.evaluate(source_code, "test.py")
        ]
        # Should detect expensive imports
        assert any(v.get("rule_id") == "AFW003" for v in violations)

    def test_scan_dag_without_violations(self, scanner):
        """Test clean DAG scanning."""
        source_code = """
from airflow import DAG
from datetime import datetime

dag = DAG(
    'clean_dag',
    start_date=datetime(2024, 1, 1),
    sla=timedelta(hours=1)
)

task1 = DummyOperator(task_id='task1', dag=dag)
task2 = DummyOperator(task_id='task2', dag=dag)
task1 >> task2
"""
        violations = [
            v for rule in scanner.dag_rules for v in rule.evaluate(source_code, "test.py")
        ]
        # Should not detect circular dependencies
        assert not any(v.get("rule_id") == "AFW001" for v in violations)

    def test_get_scorer(self, scanner):
        """Test scorer initialization."""
        scorer = scanner._get_scorer()
        assert scorer is not None

    def test_scan_config_boolean_coercion(self, scanner, tmp_path):
        """Regression test: configparser returns every value as a string, so
        "False" is truthy in plain Python. Rules like TLSConfigurationRule
        and RBACConfigurationRule do `if not enable_ssl` checks that would
        silently never fire against a real airflow.cfg without coercing
        boolean-looking strings to real bools."""
        cfg_file = tmp_path / "airflow.cfg"
        cfg_file.write_text("[webserver]\n" "enable_ssl = False\n" "rbac = False\n")

        violations = scanner.scan_config(cfg_file)

        rule_ids = {v["rule_id"] for v in violations}
        assert "CFG009" in rule_ids  # TLSConfigurationRule
        assert "CFG010" in rule_ids  # RBACConfigurationRule

    def test_scan_config_true_values_do_not_fire(self, scanner, tmp_path):
        """Sanity check the other direction of coercion: enable_ssl/rbac set
        to True (any of configparser's boolean spellings) must not trigger
        the corresponding violations."""
        cfg_file = tmp_path / "airflow.cfg"
        cfg_file.write_text("[webserver]\n" "enable_ssl = true\n" "rbac = yes\n")

        violations = scanner.scan_config(cfg_file)

        rule_ids = {v["rule_id"] for v in violations}
        assert "CFG009" not in rule_ids
        assert "CFG010" not in rule_ids
