"""
PyAirflowTester: Unified Airflow + dbt Reliability Platform

A correlation-first reliability and quality platform that combines static analysis,
runtime monitoring, and intelligent correlation to prevent data pipeline failures.
"""

__version__ = "0.5.3"
__author__ = "PyAirflowTester Contributors"
__license__ = "Apache-2.0"

try:
    from pyairflowtester._core import (
        PyCategory,
        PyDagDefinition,
        PyDagParser,
        PyDbtModel,
        PyDbtParser,
        PyDbtProject,
        PyDbtTest,
        PyExecutionMode,
        PyRule,
        PyRuleContext,
        PyRuleEngine,
        PyRuleViolation,
        PyScorer,
        PySeverity,
        evaluate_rules,
    )
except ImportError:
    # Fallback if Rust extension not available
    PyRule = None
    PyRuleViolation = None
    evaluate_rules = None
    PySeverity = None
    PyCategory = None
    PyExecutionMode = None
    PyRuleContext = None
    PyRuleEngine = None
    PyDagDefinition = None
    PyDagParser = None
    PyDbtModel = None
    PyDbtTest = None
    PyDbtProject = None
    PyDbtParser = None
    PyScorer = None

from pyairflowtester.analyzer import Analyzer, AnalyzerNotImplementedError
from pyairflowtester.column_lineage import (
    ColumnLineage,
    LineageUnavailable,
    analyze_dbt_model,
    analyze_file,
    analyze_sql,
)
from pyairflowtester.openlineage import (
    LineageStore,
    RuntimeLineageSummary,
    ingest_files,
    load_events,
)
from pyairflowtester.report import ReportGenerator
from pyairflowtester.scanner import Scanner

__all__ = [
    "Scanner",
    "Analyzer",
    "AnalyzerNotImplementedError",
    "ColumnLineage",
    "LineageUnavailable",
    "analyze_sql",
    "analyze_file",
    "analyze_dbt_model",
    "LineageStore",
    "RuntimeLineageSummary",
    "ingest_files",
    "load_events",
    "ReportGenerator",
    "PyRule",
    "PyRuleViolation",
    "evaluate_rules",
    "PySeverity",
    "PyCategory",
    "PyExecutionMode",
    "PyRuleContext",
    "PyRuleEngine",
    "PyDagDefinition",
    "PyDagParser",
    "PyDbtModel",
    "PyDbtTest",
    "PyDbtProject",
    "PyDbtParser",
    "PyScorer",
]
