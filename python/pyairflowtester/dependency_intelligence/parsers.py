"""Parsers for different dependency sources (Airflow, dbt, datasets)."""

import ast
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from .models import (
    Node,
    Edge,
    NodeType,
    NodeSeverity,
    RelationshipType,
    DependencyGraph,
)

logger = logging.getLogger(__name__)


class AirflowDAGParser:
    """Parse Airflow DAG files to extract dependencies."""

    @staticmethod
    def parse_dag_file(file_path: str) -> Tuple[Optional[str], List[str], List[Tuple[str, str]]]:
        """
        Parse a Python DAG file and extract DAG ID, task IDs, and dependencies.

        Returns:
            Tuple of (dag_id, task_ids, dependencies)
        """
        try:
            with open(file_path, 'r') as f:
                source_code = f.read()
            return AirflowDAGParser.parse_dag_code(source_code)
        except Exception as e:
            logger.error(f"Error parsing DAG file {file_path}: {e}")
            return None, [], []

    @staticmethod
    def parse_dag_code(source_code: str) -> Tuple[Optional[str], List[str], List[Tuple[str, str]]]:
        """
        Parse DAG Python code and extract DAG ID, tasks, and dependencies.

        Returns:
            Tuple of (dag_id, task_ids, dependencies)
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.error(f"Syntax error parsing DAG code: {e}")
            return None, [], []

        dag_id = None
        task_ids = set()
        dependencies = []

        class DAGVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                nonlocal dag_id

                # Look for DAG() instantiation
                if isinstance(node.func, ast.Name) and node.func.id == "DAG":
                    for keyword in node.keywords:
                        if keyword.arg == "dag_id" and isinstance(keyword.value, ast.Constant):
                            dag_id = keyword.value.value
                        elif keyword.arg == "dag_id" and isinstance(keyword.value, ast.Str):
                            dag_id = keyword.value.s

                # Look for task assignments
                if isinstance(node.func, ast.Name) and "Operator" in node.func.id:
                    for keyword in node.keywords:
                        if keyword.arg == "task_id" and isinstance(keyword.value, ast.Constant):
                            task_ids.add(keyword.value.value)
                        elif keyword.arg == "task_id" and isinstance(keyword.value, ast.Str):
                            task_ids.add(keyword.value.s)

                # Look for task dependencies (set_upstream/set_downstream)
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("set_upstream", "set_downstream"):
                        if isinstance(node.func.value, ast.Name):
                            task1 = node.func.value.id
                            if len(node.args) > 0 and isinstance(node.args[0], ast.Name):
                                task2 = node.args[0].id
                                if node.func.attr == "set_upstream":
                                    dependencies.append((task2, task1))
                                else:
                                    dependencies.append((task1, task2))

                self.generic_visit(node)

        DAGVisitor().visit(tree)

        return dag_id, sorted(list(task_ids)), dependencies

    @staticmethod
    def build_graph(dag_files: List[str]) -> DependencyGraph:
        """
        Build a dependency graph from multiple DAG files.

        Args:
            dag_files: List of paths to DAG Python files

        Returns:
            DependencyGraph with all DAGs, tasks, and dependencies
        """
        graph = DependencyGraph()
        all_dependencies = []

        for dag_file in dag_files:
            dag_id, task_ids, dependencies = AirflowDAGParser.parse_dag_file(dag_file)

            if dag_id:
                # Add DAG node
                dag_node = Node(
                    id=f"dag_{dag_id}",
                    name=dag_id,
                    type=NodeType.DAG,
                    owner="airflow",
                )
                graph.add_node(dag_node)

                # Add task nodes
                for task_id in task_ids:
                    task_node = Node(
                        id=f"task_{dag_id}_{task_id}",
                        name=f"{dag_id}.{task_id}",
                        type=NodeType.TASK,
                        owner="airflow",
                        metadata={"dag_id": dag_id, "task_id": task_id},
                    )
                    graph.add_node(task_node)

                    # Add edge from DAG to task
                    edge = Edge(
                        source=f"dag_{dag_id}",
                        target=f"task_{dag_id}_{task_id}",
                        relationship_type=RelationshipType.CALLS,
                    )
                    graph.add_edge(edge)

                # Store dependencies for later processing
                for source, target in dependencies:
                    all_dependencies.append((dag_id, source, target))

        # Add task-to-task dependencies
        for dag_id, source_task, target_task in all_dependencies:
            source_id = f"task_{dag_id}_{source_task}"
            target_id = f"task_{dag_id}_{target_task}"

            if source_id in graph.nodes and target_id in graph.nodes:
                edge = Edge(
                    source=source_id,
                    target=target_id,
                    relationship_type=RelationshipType.DEPENDS_ON,
                )
                graph.add_edge(edge)

        return graph


class dbtManifestParser:
    """Parse dbt manifest.json to extract model lineage."""

    @staticmethod
    def parse_manifest(manifest_path: str) -> DependencyGraph:
        """
        Parse dbt manifest.json and build dependency graph.

        Args:
            manifest_path: Path to manifest.json

        Returns:
            DependencyGraph with dbt models and lineage
        """
        graph = DependencyGraph()

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except Exception as e:
            logger.error(f"Error reading manifest: {e}")
            return graph

        # Parse nodes (models, tests, sources, etc.)
        nodes_data = manifest.get("nodes", {})
        metadata_nodes = manifest.get("metadata", {})

        for node_id, node_data in nodes_data.items():
            # Determine node type
            if "model." in node_id:
                node_type = NodeType.DBT_MODEL
            elif "test." in node_id:
                node_type = NodeType.DBT_TEST
            elif "source." in node_id:
                node_type = NodeType.DBT_SOURCE
            elif "snapshot." in node_id:
                node_type = NodeType.DBT_SNAPSHOT
            elif "exposure." in node_id:
                node_type = NodeType.DBT_EXPOSURE
            else:
                continue

            # Create node
            node = Node(
                id=node_id,
                name=node_data.get("name", node_id),
                type=node_type,
                owner=node_data.get("meta", {}).get("owner", "dbt"),
                description=node_data.get("description", ""),
                metadata={
                    "package": node_data.get("package_name", ""),
                    "database": node_data.get("database", ""),
                    "schema": node_data.get("schema", ""),
                    "tags": node_data.get("tags", []),
                },
            )
            graph.add_node(node)

        # Parse dependencies (edges)
        for node_id, node_data in nodes_data.items():
            depends_on = node_data.get("depends_on", {}).get("nodes", [])

            for dependency_id in depends_on:
                if dependency_id in graph.nodes:
                    edge = Edge(
                        source=dependency_id,
                        target=node_id,
                        relationship_type=RelationshipType.DEPENDS_ON,
                    )
                    graph.add_edge(edge)

        # Parse exposures
        exposures = manifest.get("exposures", {})
        for exposure_id, exposure_data in exposures.items():
            node = Node(
                id=exposure_id,
                name=exposure_data.get("name", exposure_id),
                type=NodeType.DBT_EXPOSURE,
                owner=exposure_data.get("meta", {}).get("owner", "dbt"),
                description=exposure_data.get("description", ""),
            )
            graph.add_node(node)

            for dependency_id in exposure_data.get("depends_on", {}).get("nodes", []):
                if dependency_id in graph.nodes:
                    edge = Edge(
                        source=dependency_id,
                        target=exposure_id,
                        relationship_type=RelationshipType.EXPOSES,
                    )
                    graph.add_edge(edge)

        return graph

    @staticmethod
    def parse_model_node(node_data: Dict[str, Any]) -> Node:
        """Parse a single dbt model node."""
        return Node(
            id=node_data.get("unique_id"),
            name=node_data.get("name"),
            type=NodeType.DBT_MODEL,
            owner=node_data.get("meta", {}).get("owner", "dbt"),
            description=node_data.get("description", ""),
            metadata={
                "materialized": node_data.get("config", {}).get("materialized"),
                "tags": node_data.get("tags", []),
            },
        )


class AirflowDatasetParser:
    """Parse Airflow dataset definitions and dependencies."""

    @staticmethod
    def parse_dataset_connections(source_code: str) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Parse Airflow code for dataset producers and consumers.

        Returns:
            Tuple of (dataset_ids, dependencies)
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return [], []

        datasets = set()
        dependencies = []

        class DatasetVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                # Look for Dataset() instantiation
                if isinstance(node.func, ast.Name) and node.func.id == "Dataset":
                    for keyword in node.keywords:
                        if keyword.arg == "uri" and isinstance(keyword.value, ast.Constant):
                            datasets.add(keyword.value.value)

                # Look for dataset_triggers
                if isinstance(node.func, ast.Name) and node.func.id == "DAG":
                    for keyword in node.keywords:
                        if keyword.arg == "start_date":
                            pass  # Found DAG start_date

                self.generic_visit(node)

        DatasetVisitor().visit(tree)

        return sorted(list(datasets)), dependencies

    @staticmethod
    def build_dataset_graph(airflow_files: List[str]) -> DependencyGraph:
        """
        Build dataset dependency graph from Airflow files.

        Args:
            airflow_files: List of paths to Airflow Python files

        Returns:
            DependencyGraph with datasets as nodes
        """
        graph = DependencyGraph()

        for airflow_file in airflow_files:
            try:
                with open(airflow_file, 'r') as f:
                    source_code = f.read()

                datasets, deps = AirflowDatasetParser.parse_dataset_connections(source_code)

                for dataset_uri in datasets:
                    node = Node(
                        id=f"dataset_{hash(dataset_uri)}",
                        name=dataset_uri,
                        type=NodeType.DATASET,
                        owner="airflow",
                        metadata={"uri": dataset_uri},
                    )
                    graph.add_node(node)

            except Exception as e:
                logger.error(f"Error parsing dataset file {airflow_file}: {e}")

        return graph


class UnifiedGraphBuilder:
    """Build unified graph from multiple sources (Airflow + dbt + datasets)."""

    @staticmethod
    def build_unified_graph(
        dag_files: List[str] = None,
        dbt_manifest: str = None,
        dataset_files: List[str] = None,
    ) -> DependencyGraph:
        """
        Build a unified dependency graph from multiple sources.

        Returns:
            Unified DependencyGraph
        """
        unified_graph = DependencyGraph()

        # Parse Airflow DAGs
        if dag_files:
            dag_graph = AirflowDAGParser.build_graph(dag_files)
            unified_graph.nodes.update(dag_graph.nodes)
            unified_graph.edges.extend(dag_graph.edges)

        # Parse dbt manifest
        if dbt_manifest and Path(dbt_manifest).exists():
            dbt_graph = dbtManifestParser.parse_manifest(dbt_manifest)
            unified_graph.nodes.update(dbt_graph.nodes)
            unified_graph.edges.extend(dbt_graph.edges)

        # Parse datasets
        if dataset_files:
            dataset_graph = AirflowDatasetParser.build_dataset_graph(dataset_files)
            unified_graph.nodes.update(dataset_graph.nodes)
            unified_graph.edges.extend(dataset_graph.edges)

        return unified_graph
