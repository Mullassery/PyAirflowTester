"""Tests for scanner module."""

import pytest
from pathlib import Path
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

    def test_scan_dag_with_circular_dependency(self, scanner):
        """Test circular dependency detection."""
        source_code = """
from airflow import DAG
task1 >> task2 >> task3 >> task1
"""
        violations = [v for rule in scanner.dag_rules for v in rule.evaluate(source_code, "test.py")]
        # Should detect circular dependency
        assert any(v.get("rule_id") == "AFW001" for v in violations)

    def test_scan_dag_missing_sla(self, scanner):
        """Test missing SLA detection."""
        source_code = """
from airflow import DAG
dag = DAG('production_dag', catchup=False)
"""
        violations = [v for rule in scanner.dag_rules for v in rule.evaluate(source_code, "production_test.py")]
        # Should detect missing SLA on production DAG
        assert any(v.get("rule_id") == "AFW002" for v in violations)

    def test_scan_dag_expensive_imports(self, scanner):
        """Test expensive imports detection."""
        source_code = """
import tensorflow as tf
from airflow import DAG
"""
        violations = [v for rule in scanner.dag_rules for v in rule.evaluate(source_code, "test.py")]
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
        violations = [v for rule in scanner.dag_rules for v in rule.evaluate(source_code, "test.py")]
        # Should not detect circular dependencies
        assert not any(v.get("rule_id") == "AFW001" for v in violations)

    def test_get_scorer(self, scanner):
        """Test scorer initialization."""
        scorer = scanner._get_scorer()
        assert scorer is not None
