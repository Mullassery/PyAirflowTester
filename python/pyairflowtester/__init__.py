"""
PyAirflowTester: Unified Airflow + dbt Reliability Platform

A correlation-first reliability and quality platform that combines static analysis,
runtime monitoring, and intelligent correlation to prevent data pipeline failures.
"""

__version__ = "0.5.4"
__author__ = "PyAirflowTester Contributors"
__license__ = "Apache-2.0"

from pyairflowtester.analyzer import Analyzer, AnalyzerNotImplementedError
from pyairflowtester.column_lineage import (
    ColumnLineage,
    LineageUnavailable,
    analyze_dbt_model,
    analyze_file,
    analyze_sql,
)
from pyairflowtester.dag_parser import (
    DagParser,
    parse_dag_code,
    parse_dag_directory,
    parse_dag_file,
)
from pyairflowtester.models import DagDefinition
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
    "DagParser",
    "DagDefinition",
    "parse_dag_code",
    "parse_dag_file",
    "parse_dag_directory",
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
]
