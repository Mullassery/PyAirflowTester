"""Tests for the Python AST DAG parser (`pyairflowtester.dag_parser`).

These cover the three metadata fields previously only computed by the
unshipped Rust parser: max task depth, dynamic-DAG detection, and external
system dependencies. Fixtures are intentionally small, valid DAG modules.
"""

import json

import pytest
from click.testing import CliRunner
from pyairflowtester import DagParser, parse_dag_code
from pyairflowtester.cli import main

LINEAR_DAG = """
from airflow import DAG
from airflow.operators.python import PythonOperator

dag = DAG("linear_dag", schedule=None)
extract = PythonOperator(task_id="extract", dag=dag)
transform = PythonOperator(task_id="transform", dag=dag)
load = PythonOperator(task_id="load", dag=dag)

extract >> transform >> load
"""

BRANCHING_DAG = """
from airflow import DAG
from airflow.operators.bash import BashOperator

dag = DAG("branching_dag")
start = BashOperator(task_id="start", dag=dag)
extract_a = BashOperator(task_id="extract_a", dag=dag)
extract_b = BashOperator(task_id="extract_b", dag=dag)
transform = BashOperator(task_id="transform", dag=dag)
load = BashOperator(task_id="load", dag=dag)

start >> [extract_a, extract_b]
extract_a >> transform
transform >> load
extract_b >> load
"""

EXTERNAL_DAG = """
import requests
from airflow import DAG
from airflow.providers.amazon.aws.operators.s3 import S3CreateObjectOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

dag = DAG("external_dag")
s3_task = S3CreateObjectOperator(task_id="upload", conn_id="aws_default", dag=dag)
snowflake_task = SnowflakeOperator(task_id="snowflake", conn_id="snowflake_prod", dag=dag)
postgres_task = SQLExecuteQueryOperator(
    task_id="postgres", conn_id="postgres_default", sql="SELECT 1", dag=dag
)
bigquery_task = SQLExecuteQueryOperator(
    task_id="bigquery", sql="SELECT * FROM bigquery.dataset.table", dag=dag
)
mysql_task = SQLExecuteQueryOperator(
    task_id="mysql", conn_id="mysql_default", sql="SELECT 1", dag=dag
)
redshift_task = SQLExecuteQueryOperator(
    task_id="redshift", sql="SELECT * FROM redshift.public.events", dag=dag
)
api_task = requests.get("https://example.com/status")
"""


class TestMaxTaskDepth:
    def test_linear_dag(self):
        dag = parse_dag_code(LINEAR_DAG, "linear_dag.py")
        assert dag.dag_id == "linear_dag"
        assert dag.task_ids == ["extract", "load", "transform"]
        assert dag.max_task_depth == 3
        assert dag.has_cycles is False

    def test_branching_dag_uses_longest_chain(self):
        dag = parse_dag_code(BRANCHING_DAG, "branching_dag.py")
        # start -> extract_a -> transform -> load is the longest chain.
        assert dag.max_task_depth == 4

    def test_list_operands_and_shift_left(self):
        source = """
a = BashOperator(task_id="a")
b = BashOperator(task_id="b")
c = BashOperator(task_id="c")
c << b << a
"""
        assert parse_dag_code(source).max_task_depth == 3

    def test_set_upstream_and_downstream(self):
        source = """
a = BashOperator(task_id="a")
b = BashOperator(task_id="b")
c = BashOperator(task_id="c")
b.set_upstream(a)
a.set_downstream(b)
b.set_downstream(c)
"""
        assert parse_dag_code(source).max_task_depth == 3

    def test_no_tasks_is_zero(self):
        assert parse_dag_code('dag_id = "empty"\n').max_task_depth == 0

    def test_independent_tasks_are_one(self):
        source = """
a = BashOperator(task_id="a")
b = BashOperator(task_id="b")
"""
        dag = parse_dag_code(source)
        assert dag.task_count == 2
        assert dag.max_task_depth == 1


class TestDynamicDagDetection:
    @pytest.mark.parametrize(
        "source",
        [
            'for table in ["a", "b"]:\n    create_task(table)\n',
            "while ready:\n    pass\n",
            'globals()["generated_task"] = build_task()\n',
            "@task_group\ndef group():\n    pass\n",
            "mapped = build_task.expand(value=[1, 2, 3])\n",
        ],
    )
    def test_detects_dynamic_constructs(self, source):
        assert parse_dag_code(source).dynamic_dag_detected is True

    def test_static_dag_is_not_dynamic(self):
        assert parse_dag_code(LINEAR_DAG).dynamic_dag_detected is False


class TestExternalDependencies:
    def test_operators_conn_ids_sql_and_urls(self):
        dag = parse_dag_code(EXTERNAL_DAG, "external_dag.py")
        assert dag.external_dependencies == [
            "S3",
            "BigQuery",
            "Snowflake",
            "PostgreSQL",
            "MySQL",
            "Redshift",
            "API",
        ]

    def test_comments_and_docstrings_are_ignored(self):
        source = '''
"""This docstring mentions snowflake and s3://bucket but is not an operator."""
dag = DAG("clean")
# bigquery and postgres appear only in this comment
'''
        assert parse_dag_code(source).external_dependencies == []

    def test_linear_dag_has_no_external_dependencies(self):
        assert parse_dag_code(LINEAR_DAG).external_dependencies == []


class TestDagParserFiles:
    def test_parse_file_and_directory(self, tmp_path):
        (tmp_path / "linear_dag.py").write_text(LINEAR_DAG)
        (tmp_path / "_private.py").write_text("this is not: valid python !!!")

        parser = DagParser()
        dag = parser.parse_file(tmp_path / "linear_dag.py")
        dags = parser.parse_directory(tmp_path)

        assert dag.dag_id == "linear_dag"
        assert len(dags) == 1
        assert dags[0].max_task_depth == 3
        assert dags[0].parse_time_ms >= 0.0

    def test_to_dict_includes_new_fields(self):
        payload = parse_dag_code(EXTERNAL_DAG).to_dict()
        assert payload["max_task_depth"] == 1
        assert payload["dynamic_dag_detected"] is False
        assert "Snowflake" in payload["external_dependencies"]

    def test_cli_json_output(self, tmp_path):
        (tmp_path / "linear_dag.py").write_text(LINEAR_DAG)

        result = CliRunner().invoke(main, ["parse-dags", str(tmp_path), "--format", "json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["dags"][0]["dag_id"] == "linear_dag"
        assert payload["dags"][0]["max_task_depth"] == 3
        assert payload["dags"][0]["dynamic_dag_detected"] is False
        assert payload["dags"][0]["external_dependencies"] == []
