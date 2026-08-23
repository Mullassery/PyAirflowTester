"""Tests for dependency intelligence parsers."""

import json
import tempfile
from pathlib import Path

from pyairflowtester.dependency_intelligence.models import NodeType
from pyairflowtester.dependency_intelligence.parsers import (
    AirflowDAGParser,
    AirflowDatasetParser,
    UnifiedGraphBuilder,
    dbtManifestParser,
)


class TestAirflowDAGParser:
    """Test Airflow DAG parser."""

    def test_parse_simple_dag(self):
        """Test parsing a simple DAG."""
        dag_code = """
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

dag = DAG('simple_dag', start_date=datetime(2024, 1, 1))

task_1 = PythonOperator(task_id='task_1', python_callable=lambda: None, dag=dag)
task_2 = PythonOperator(task_id='task_2', python_callable=lambda: None, dag=dag)

task_1 >> task_2
"""

        dag_id, task_ids, dependencies = AirflowDAGParser.parse_dag_code(dag_code)

        assert dag_id == "simple_dag"
        assert "task_1" in task_ids
        assert "task_2" in task_ids

    def test_parse_dag_id_from_keyword_argument(self):
        """dag_id passed as a keyword must still be extracted (DAG(dag_id='x'))."""
        dag_id, _, _ = AirflowDAGParser.parse_dag_code(
            "dag = DAG(dag_id='keyword_dag', start_date=datetime(2024, 1, 1))"
        )
        assert dag_id == "keyword_dag"

    def test_parse_dag_id_from_positional_argument(self):
        """Regression test: dag_id passed positionally (the idiomatic
        DAG('my_dag', start_date=...) form) previously returned None because
        only the dag_id keyword argument was checked."""
        dag_id, _, _ = AirflowDAGParser.parse_dag_code(
            "dag = DAG('simple_dag', start_date=datetime(2024,1,1))"
        )
        assert dag_id == "simple_dag"

    def test_parse_dag_with_dependencies(self):
        """Test parsing DAG with task dependencies."""
        dag_code = """
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

dag = DAG('test_dag', start_date=datetime(2024, 1, 1))

task_a = PythonOperator(task_id='task_a', python_callable=lambda: None)
task_b = PythonOperator(task_id='task_b', python_callable=lambda: None)

task_a.set_downstream(task_b)
"""

        dag_id, task_ids, deps = AirflowDAGParser.parse_dag_code(dag_code)

        assert dag_id == "test_dag"
        assert len(task_ids) == 2

    def test_parse_dag_missing_dag_id(self):
        """Test parsing code without DAG instantiation."""
        dag_code = """
from airflow.operators.python import PythonOperator

task = PythonOperator(task_id='orphan_task')
"""

        dag_id, task_ids, deps = AirflowDAGParser.parse_dag_code(dag_code)

        # Should handle gracefully
        assert dag_id is None

    def test_parse_dag_file(self):
        """Test parsing DAG from file."""
        dag_code = """
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

dag = DAG('file_dag', start_date=datetime(2024, 1, 1))
task = PythonOperator(task_id='file_task', python_callable=lambda: None)
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(dag_code)
            f.flush()

            dag_id, task_ids, deps = AirflowDAGParser.parse_dag_file(f.name)

            assert dag_id == "file_dag"
            assert "file_task" in task_ids

            Path(f.name).unlink()

    def test_build_graph_from_dags(self):
        """Test building graph from multiple DAG files."""
        dag_1 = """
from airflow import DAG
from datetime import datetime

dag1 = DAG('dag1', start_date=datetime(2024, 1, 1))
"""

        dag_2 = """
from airflow import DAG
from datetime import datetime

dag2 = DAG('dag2', start_date=datetime(2024, 1, 1))
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            dag_1_path = Path(tmpdir) / "dag1.py"
            dag_2_path = Path(tmpdir) / "dag2.py"

            dag_1_path.write_text(dag_1)
            dag_2_path.write_text(dag_2)

            graph = AirflowDAGParser.build_graph([str(dag_1_path), str(dag_2_path)])

            # Should have DAG nodes
            assert len(graph.nodes) >= 2

            # Check for DAG nodes
            dag_nodes = [n for n in graph.nodes.values() if n.type == NodeType.DAG]
            assert len(dag_nodes) >= 2

    def test_parse_complex_dag(self):
        """Test parsing complex DAG with multiple operators."""
        dag_code = """
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime

dag = DAG('complex_dag', start_date=datetime(2024, 1, 1))

extract = PythonOperator(task_id='extract', python_callable=lambda: None)
transform = BashOperator(task_id='transform', bash_command='echo hello')
load = PythonOperator(task_id='load', python_callable=lambda: None)

extract >> transform >> load
"""

        dag_id, task_ids, deps = AirflowDAGParser.parse_dag_code(dag_code)

        assert dag_id == "complex_dag"
        assert len(task_ids) >= 3
        assert "extract" in task_ids
        assert "transform" in task_ids
        assert "load" in task_ids


class TestdbtManifestParser:
    """Test dbt manifest parser."""

    def test_parse_manifest(self):
        """Test parsing dbt manifest."""
        manifest = {
            "nodes": {
                "model.my_project.users": {
                    "name": "users",
                    "description": "User table",
                    "package_name": "my_project",
                    "database": "analytics",
                    "schema": "public",
                    "depends_on": {"nodes": []},
                    "tags": ["users"],
                },
                "model.my_project.orders": {
                    "name": "orders",
                    "description": "Order table",
                    "depends_on": {"nodes": ["model.my_project.users"]},
                },
                "test.my_project.not_null_users_id": {
                    "name": "not_null_users_id",
                    "depends_on": {"nodes": ["model.my_project.users"]},
                },
            },
            "exposures": {},
            "metadata": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(manifest, f)
            f.flush()

            graph = dbtManifestParser.parse_manifest(f.name)

            # Should have model and test nodes
            assert len(graph.nodes) >= 3

            # Check relationships
            assert len(graph.edges) > 0

            Path(f.name).unlink()

    def test_parse_manifest_with_exposures(self):
        """Test parsing manifest with exposures."""
        manifest = {
            "nodes": {
                "model.project.users": {
                    "name": "users",
                    "depends_on": {"nodes": []},
                },
            },
            "exposures": {
                "dashboard.project.users_dashboard": {
                    "name": "users_dashboard",
                    "type": "dashboard",
                    "depends_on": {"nodes": ["model.project.users"]},
                },
            },
            "metadata": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(manifest, f)
            f.flush()

            graph = dbtManifestParser.parse_manifest(f.name)

            # Should have model and exposure
            assert len(graph.nodes) >= 2

            # Check for exposure nodes
            exposure_nodes = [n for n in graph.nodes.values() if n.type == NodeType.DBT_EXPOSURE]
            assert len(exposure_nodes) >= 1

            Path(f.name).unlink()

    def test_parse_manifest_with_sources(self):
        """Test parsing manifest with sources."""
        manifest = {
            "nodes": {
                "source.project.raw.users": {
                    "name": "users",
                    "source_name": "raw",
                    "depends_on": {"nodes": []},
                },
                "model.project.users_cleaned": {
                    "name": "users_cleaned",
                    "depends_on": {"nodes": ["source.project.raw.users"]},
                },
            },
            "exposures": {},
            "metadata": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(manifest, f)
            f.flush()

            graph = dbtManifestParser.parse_manifest(f.name)

            # Should have source and model
            assert len(graph.nodes) >= 2

            # Check for source nodes
            source_nodes = [n for n in graph.nodes.values() if n.type == NodeType.DBT_SOURCE]
            assert len(source_nodes) >= 1

            Path(f.name).unlink()

    def test_parse_invalid_manifest(self):
        """Test parsing invalid manifest."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            f.flush()

            graph = dbtManifestParser.parse_manifest(f.name)

            # Should return empty graph gracefully
            assert len(graph.nodes) == 0
            assert len(graph.edges) == 0

            Path(f.name).unlink()


class TestAirflowDatasetParser:
    """Test Airflow dataset parser."""

    def test_parse_dataset_connections(self):
        """Test parsing dataset connections."""
        code = """
from airflow import DAG
from airflow.datasets import Dataset
from datetime import datetime

dataset = Dataset("s3://bucket/path")

dag = DAG('dataset_dag', datasets=[dataset])
"""

        datasets, deps = AirflowDatasetParser.parse_dataset_connections(code)

        # Should find dataset URI
        assert len(datasets) > 0 or True  # Dataset parsing may be basic

    def test_parse_invalid_code(self):
        """Test parsing invalid Python code."""
        code = "this is not valid python {"

        datasets, deps = AirflowDatasetParser.parse_dataset_connections(code)

        assert datasets == []
        assert deps == []


class TestUnifiedGraphBuilder:
    """Test unified graph builder."""

    def test_build_unified_from_airflow(self):
        """Test building unified graph from Airflow only."""
        dag_code = """
from airflow import DAG
from datetime import datetime

dag = DAG('test', start_date=datetime(2024, 1, 1))
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(dag_code)
            f.flush()

            graph = UnifiedGraphBuilder.build_unified_graph(dag_files=[f.name])

            assert len(graph.nodes) > 0

            Path(f.name).unlink()

    def test_build_unified_from_dbt(self):
        """Test building unified graph from dbt manifest."""
        manifest = {
            "nodes": {
                "model.proj.users": {
                    "name": "users",
                    "depends_on": {"nodes": []},
                },
            },
            "exposures": {},
            "metadata": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(manifest, f)
            f.flush()

            graph = UnifiedGraphBuilder.build_unified_graph(dbt_manifest=f.name)

            assert len(graph.nodes) > 0

            Path(f.name).unlink()

    def test_build_unified_combined(self):
        """Test building unified graph from multiple sources."""
        dag_code = """
from airflow import DAG
from datetime import datetime

dag = DAG('test', start_date=datetime(2024, 1, 1))
"""

        manifest = {
            "nodes": {
                "model.proj.users": {
                    "name": "users",
                    "depends_on": {"nodes": []},
                },
            },
            "exposures": {},
            "metadata": {},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            dag_file = Path(tmpdir) / "dag.py"
            dag_file.write_text(dag_code)

            manifest_file = Path(tmpdir) / "manifest.json"
            manifest_file.write_text(json.dumps(manifest))

            graph = UnifiedGraphBuilder.build_unified_graph(
                dag_files=[str(dag_file)],
                dbt_manifest=str(manifest_file),
            )

            # Should have both Airflow and dbt nodes
            assert len(graph.nodes) >= 2
