"""Tests for the sandboxed runtime-import fallback (runtime_import.py).

Real `apache-airflow` is a heavy, non-trivial-to-pin dependency this
otherwise dependency-light package doesn't take on (it's opt-in, per
runtime_import.py's own docstring). These tests use a small fake `airflow`
package as a stand-in so the actual mechanism under test -- subprocess
sandboxing, the JSON hand-back contract, and resolving a *dynamically*
built task graph after real execution -- is exercised end to end without
requiring the real package to be installed.
"""

import os
import textwrap

import pytest
from pyairflowtester.dependency_intelligence.runtime_import import (
    parse_dag_file_with_fallback,
    parse_dag_via_runtime_import,
)

_FAKE_AIRFLOW_PACKAGE = textwrap.dedent(
    """
    class DAG:
        def __init__(self, dag_id):
            self.dag_id = dag_id
            self.task_dict = {}

        def add_task(self, task):
            self.task_dict[task.task_id] = task


    class BaseOperator:
        def __init__(self, task_id, dag):
            self.task_id = task_id
            self.dag = dag
            self.upstream_task_ids = set()
            dag.add_task(self)

        def set_upstream(self, other):
            self.upstream_task_ids.add(other.task_id)

        def __rshift__(self, other):
            other.upstream_task_ids.add(self.task_id)
            return other
    """
)


@pytest.fixture
def fake_airflow_on_path(tmp_path, monkeypatch):
    """Install a minimal fake `airflow`/`airflow.models` package onto
    PYTHONPATH so the sandboxed subprocess (which inherits the environment)
    can `import airflow` / `from airflow.models import DAG` for real."""
    airflow_dir = tmp_path / "fake_site_packages" / "airflow"
    models_dir = airflow_dir / "models"
    models_dir.mkdir(parents=True)
    (airflow_dir / "__init__.py").write_text("")
    (models_dir / "__init__.py").write_text(_FAKE_AIRFLOW_PACKAGE)

    fake_site_packages = str(tmp_path / "fake_site_packages")
    existing = os.environ.get("PYTHONPATH", "")
    monkeypatch.setenv(
        "PYTHONPATH", fake_site_packages + (os.pathsep + existing if existing else "")
    )
    return fake_site_packages


class TestRuntimeImportWithoutAirflow:
    def test_reports_airflow_not_installed_gracefully(self, tmp_path, monkeypatch):
        # Ensure no fake/real airflow leaks in from a prior test or the environment.
        monkeypatch.delenv("PYTHONPATH", raising=False)
        dag_file = tmp_path / "dag.py"
        dag_file.write_text("# no airflow available in this environment\n")

        dag_id, task_ids, deps = parse_dag_via_runtime_import(str(dag_file))

        assert dag_id is None
        assert task_ids == []
        assert deps == []

    def test_does_not_raise_on_nonexistent_file(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PYTHONPATH", raising=False)
        dag_id, task_ids, deps = parse_dag_via_runtime_import(str(tmp_path / "missing.py"))
        assert (dag_id, task_ids, deps) == (None, [], [])


class TestRuntimeImportResolvesDynamicDags:
    def test_resolves_tasks_built_in_a_for_loop(self, tmp_path, fake_airflow_on_path):
        """This is exactly the case AirflowDAGParser's static AST parser
        can't see: task_id strings only exist after the loop runs."""
        dag_file = tmp_path / "dynamic_dag.py"
        dag_file.write_text(
            textwrap.dedent(
                """
                from airflow.models import DAG, BaseOperator

                dag = DAG(dag_id="dynamic_fanout")
                tasks = []
                for i in range(5):
                    t = BaseOperator(task_id=f"task_{i}", dag=dag)
                    tasks.append(t)
                for upstream, downstream in zip(tasks, tasks[1:]):
                    upstream >> downstream
                """
            )
        )

        dag_id, task_ids, deps = parse_dag_via_runtime_import(str(dag_file))

        assert dag_id == "dynamic_fanout"
        assert task_ids == [f"task_{i}" for i in range(5)]
        assert set(deps) == {
            ("task_0", "task_1"),
            ("task_1", "task_2"),
            ("task_2", "task_3"),
            ("task_3", "task_4"),
        }

    def test_resolves_tasks_built_via_factory_function(self, tmp_path, fake_airflow_on_path):
        dag_file = tmp_path / "factory_dag.py"
        dag_file.write_text(
            textwrap.dedent(
                """
                from airflow.models import DAG, BaseOperator

                def build_dag():
                    dag = DAG(dag_id="factory_built")
                    extract = BaseOperator(task_id="extract", dag=dag)
                    load = BaseOperator(task_id="load", dag=dag)
                    load.set_upstream(extract)
                    return dag

                dag = build_dag()
                """
            )
        )

        dag_id, task_ids, deps = parse_dag_via_runtime_import(str(dag_file))

        assert dag_id == "factory_built"
        assert task_ids == ["extract", "load"]
        assert deps == [("extract", "load")]

    def test_reports_no_dag_found_when_module_defines_none(self, tmp_path, fake_airflow_on_path):
        dag_file = tmp_path / "not_a_dag.py"
        dag_file.write_text("x = 1 + 1\n")

        dag_id, task_ids, deps = parse_dag_via_runtime_import(str(dag_file))

        assert (dag_id, task_ids, deps) == (None, [], [])

    def test_import_error_in_dag_file_does_not_crash_caller(self, tmp_path, fake_airflow_on_path):
        dag_file = tmp_path / "broken_dag.py"
        dag_file.write_text("raise RuntimeError('boom during import')\n")

        dag_id, task_ids, deps = parse_dag_via_runtime_import(str(dag_file))

        assert (dag_id, task_ids, deps) == (None, [], [])

    def test_is_sandboxed_in_a_separate_process(self, tmp_path, fake_airflow_on_path):
        """A DAG file that mutates its own process (env var) must not affect
        the caller's process -- proof this actually runs in a subprocess."""
        dag_file = tmp_path / "mutates_process.py"
        dag_file.write_text(
            textwrap.dedent(
                """
                import os
                os.environ["PYAIRFLOWTESTER_SANDBOX_CANARY"] = "leaked"
                from airflow.models import DAG, BaseOperator
                dag = DAG(dag_id="canary_dag")
                BaseOperator(task_id="t1", dag=dag)
                """
            )
        )

        os.environ.pop("PYAIRFLOWTESTER_SANDBOX_CANARY", None)
        dag_id, task_ids, deps = parse_dag_via_runtime_import(str(dag_file))

        assert dag_id == "canary_dag"
        assert "PYAIRFLOWTESTER_SANDBOX_CANARY" not in os.environ

    def test_timeout_is_enforced(self, tmp_path, fake_airflow_on_path):
        dag_file = tmp_path / "slow_dag.py"
        dag_file.write_text(
            textwrap.dedent(
                """
                import time
                time.sleep(5)
                from airflow.models import DAG
                dag = DAG(dag_id="never_gets_here")
                """
            )
        )

        dag_id, task_ids, deps = parse_dag_via_runtime_import(str(dag_file), timeout_seconds=0.5)

        assert (dag_id, task_ids, deps) == (None, [], [])


class TestParseDagFileWithFallback:
    def test_uses_static_parser_result_when_it_finds_tasks(self, tmp_path):
        dag_file = tmp_path / "static_dag.py"
        dag_file.write_text(
            textwrap.dedent(
                """
                from airflow import DAG
                from airflow.operators.bash import BashOperator

                dag = DAG('static_dag')
                t1 = BashOperator(task_id='t1', bash_command='echo 1')
                t2 = BashOperator(task_id='t2', bash_command='echo 2')
                t1.set_downstream(t2)
                """
            )
        )

        dag_id, task_ids, deps = parse_dag_file_with_fallback(str(dag_file))

        assert dag_id == "static_dag"
        assert set(task_ids) == {"t1", "t2"}

    def test_falls_back_to_runtime_import_when_static_parser_finds_nothing(
        self, tmp_path, fake_airflow_on_path
    ):
        dag_file = tmp_path / "dynamic_only.py"
        dag_file.write_text(
            textwrap.dedent(
                """
                from airflow.models import DAG, BaseOperator

                dag = DAG(dag_id="fallback_target")
                for i in range(3):
                    BaseOperator(task_id=f"gen_{i}", dag=dag)
                """
            )
        )

        dag_id, task_ids, deps = parse_dag_file_with_fallback(str(dag_file))

        # Static AST parsing finds nothing here (no literal DAG()/Operator() calls
        # with string task_id keywords), so this proves the fallback actually ran.
        assert dag_id == "fallback_target"
        assert task_ids == ["gen_0", "gen_1", "gen_2"]
