"""
PyAirflowTester: Unified Airflow + dbt Reliability Platform

A correlation-first reliability and quality platform that combines static analysis,
runtime monitoring, and intelligent correlation to prevent data pipeline failures.
"""

__version__ = "0.2.0"
__author__ = "PyAirflowTester Contributors"
__license__ = "SSPL-1.0"

try:
    from pyairflowtester._core import (
        PyRule,
        PyRuleViolation,
        evaluate_rules,
        PySeverity,
        PyCategory,
        PyExecutionMode,
        PyRuleContext,
        PyRuleEngine,
        PyDagDefinition,
        PyDagParser,
        PyDbtModel,
        PyDbtTest,
        PyDbtProject,
        PyDbtParser,
        PyScorer,
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

from pyairflowtester.scanner import Scanner
from pyairflowtester.analyzer import Analyzer
from pyairflowtester.report import ReportGenerator

__all__ = [
    "Scanner",
    "Analyzer",
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
