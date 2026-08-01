"""CLI commands for dependency intelligence."""

import json
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from .graph import DependencyGraphEngine
from .parsers import AirflowDAGParser, dbtManifestParser, UnifiedGraphBuilder
from .analyzers import (
    ImpactAnalysisEngine,
    BlastRadiusEngine,
    RiskScoringEngine,
    DriftDetectionEngine,
)
from .models import NodeSeverity, NodeType

console = Console()
logger = logging.getLogger(__name__)


@click.group()
def dependency_cli():
    """Dependency Intelligence commands."""
    pass


@dependency_cli.command()
@click.option("--dags", type=click.Path(), help="Path to DAGs directory")
@click.option("--dbt-manifest", type=click.Path(), help="Path to dbt manifest.json")
@click.option("--datasets", type=click.Path(), help="Path to datasets directory")
@click.option("--output", type=click.File("w"), default="-", help="Output file")
def build(dags: Optional[str], dbt_manifest: Optional[str], datasets: Optional[str], output):
    """Build dependency graph from sources."""
    console.print("[bold]Building dependency graph...[/bold]")

    # Collect DAG files
    dag_files = []
    if dags:
        dag_path = Path(dags)
        dag_files = list(dag_path.glob("**/*.py"))

    # Build unified graph
    graph = UnifiedGraphBuilder.build_unified_graph(
        dag_files=[str(f) for f in dag_files],
        dbt_manifest=dbt_manifest,
        dataset_files=[],
    )

    # Display stats
    stats = graph.stats()
    console.print(
        Panel(
            f"[bold]Graph built successfully[/bold]\n"
            f"Nodes: {stats['node_count']}\n"
            f"Edges: {stats['edge_count']}\n"
            f"Critical: {stats['critical_nodes']}",
            title="Graph Statistics",
        )
    )

    # Output graph
    output.write(json.dumps(
        {
            "nodes": {
                k: {
                    "id": v.id,
                    "name": v.name,
                    "type": v.type.value,
                    "owner": v.owner,
                    "severity": v.severity.value,
                }
                for k, v in graph.nodes.items()
            },
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "relationship_type": e.relationship_type.value,
                }
                for e in graph.edges
            ],
            "stats": stats,
        },
        indent=2,
    ))


@dependency_cli.command()
@click.argument("node_id")
@click.option("--depth", type=int, default=None, help="Max traversal depth")
@click.option("--dags", type=click.Path(), help="Path to DAGs directory")
@click.option("--dbt-manifest", type=click.Path(), help="Path to dbt manifest.json")
def impact(node_id: str, depth: Optional[int], dags: Optional[str], dbt_manifest: Optional[str]):
    """Analyze impact of changing a node."""
    # Build graph
    dag_files = []
    if dags:
        dag_path = Path(dags)
        dag_files = list(dag_path.glob("**/*.py"))

    graph = UnifiedGraphBuilder.build_unified_graph(
        dag_files=[str(f) for f in dag_files],
        dbt_manifest=dbt_manifest,
    )

    # Run impact analysis
    engine = ImpactAnalysisEngine(graph)
    result = engine.analyze(node_id, max_depth=depth)

    # Display results
    console.print(
        Panel(
            f"[bold]Impact Analysis: {node_id}[/bold]\n"
            f"Impacted Nodes: {result.impact_depth}\n"
            f"Impact Score: {result.impact_score:.2f}\n"
            f"Affected: {len(result.impacted_nodes)}",
            title="Impact Analysis",
        )
    )

    # Show affected nodes by severity
    if result.by_severity:
        console.print("\n[bold]By Severity:[/bold]")
        for severity in [NodeSeverity.CRITICAL, NodeSeverity.HIGH, NodeSeverity.MEDIUM, NodeSeverity.LOW]:
            nodes = result.by_severity.get(severity, [])
            if nodes:
                console.print(f"  {severity.value.upper()}: {len(nodes)}")


@dependency_cli.command()
@click.option("--dags", type=click.Path(), help="Path to DAGs directory")
@click.option("--dbt-manifest", type=click.Path(), help="Path to dbt manifest.json")
@click.option("--format", type=click.Choice(["text", "mermaid", "graphviz"]), default="text")
def lineage(dags: Optional[str], dbt_manifest: Optional[str], format: str):
    """Show dependency lineage."""
    # Build graph
    dag_files = []
    if dags:
        dag_path = Path(dags)
        dag_files = list(dag_path.glob("**/*.py"))

    graph = UnifiedGraphBuilder.build_unified_graph(
        dag_files=[str(f) for f in dag_files],
        dbt_manifest=dbt_manifest,
    )

    if format == "mermaid":
        # Output Mermaid diagram
        console.print("```mermaid")
        console.print("graph TD")
        for edge in graph.edges[:50]:  # Limit to first 50 edges
            source = graph.nodes.get(edge.source, None)
            target = graph.nodes.get(edge.target, None)
            if source and target:
                console.print(f"  {source.name} --> {target.name}")
        console.print("```")
    else:
        # Text format
        table = Table(title="Dependencies")
        table.add_column("Source", style="cyan")
        table.add_column("Target", style="magenta")
        table.add_column("Type", style="green")

        for edge in graph.edges[:20]:  # Show first 20
            source = graph.nodes.get(edge.source, None)
            target = graph.nodes.get(edge.target, None)
            if source and target:
                table.add_row(source.name, target.name, edge.relationship_type.value)

        console.print(table)


@dependency_cli.command()
@click.option("--nodes", "-n", multiple=True, required=True, help="Nodes that changed")
@click.option("--dags", type=click.Path(), help="Path to DAGs directory")
@click.option("--dbt-manifest", type=click.Path(), help="Path to dbt manifest.json")
def blast_radius(nodes: tuple, dags: Optional[str], dbt_manifest: Optional[str]):
    """Analyze blast radius of changes."""
    # Build graph
    dag_files = []
    if dags:
        dag_path = Path(dags)
        dag_files = list(dag_path.glob("**/*.py"))

    graph = UnifiedGraphBuilder.build_unified_graph(
        dag_files=[str(f) for f in dag_files],
        dbt_manifest=dbt_manifest,
    )

    # Run blast radius analysis
    engine = BlastRadiusEngine(graph)
    result = engine.analyze(list(nodes))

    # Display results
    console.print(
        Panel(
            f"[bold]Blast Radius Analysis[/bold]\n"
            f"Changed Nodes: {len(result.change_nodes)}\n"
            f"Affected Nodes: {result.blast_radius}\n"
            f"Blast Depth: {result.blast_depth}\n"
            f"Risk Level: {result.risk_level.upper()}\n"
            f"Deployable: {'✓' if result.deployable else '✗'}",
            title="Blast Radius",
            border_style="red" if not result.deployable else "green",
        )
    )

    # Show severity distribution
    if result.severity_distribution:
        console.print("\n[bold]Severity Distribution:[/bold]")
        for severity, count in sorted(result.severity_distribution.items(),
                                     key=lambda x: x[0].value, reverse=True):
            console.print(f"  {severity.value.upper()}: {count}")


@dependency_cli.command()
@click.option("--dags", type=click.Path(), help="Path to DAGs directory")
@click.option("--dbt-manifest", type=click.Path(), help="Path to dbt manifest.json")
def detect_cycles(dags: Optional[str], dbt_manifest: Optional[str]):
    """Detect circular dependencies."""
    # Build graph
    dag_files = []
    if dags:
        dag_path = Path(dags)
        dag_files = list(dag_path.glob("**/*.py"))

    graph = UnifiedGraphBuilder.build_unified_graph(
        dag_files=[str(f) for f in dag_files],
        dbt_manifest=dbt_manifest,
    )

    # Run cycle detection
    engine = DependencyGraphEngine(graph)
    cycles = engine.detect_cycles()

    if cycles:
        console.print(
            Panel(
                f"[bold red]⚠ Found {len(cycles)} circular dependencies[/bold red]",
                title="Cycle Detection",
            )
        )

        table = Table(title="Cycles")
        table.add_column("Cycle #", style="cyan")
        table.add_column("Path", style="magenta")

        for i, cycle in enumerate(cycles, 1):
            path_str = " → ".join([graph.nodes.get(n, None).name if graph.nodes.get(n) else n for n in cycle[:5]])
            if len(cycle) > 5:
                path_str += f" ... (+{len(cycle) - 5} more)"
            table.add_row(str(i), path_str)

        console.print(table)
    else:
        console.print("[bold green]✓ No circular dependencies detected[/bold green]")


@dependency_cli.command()
@click.option("--dags", type=click.Path(), help="Path to DAGs directory")
@click.option("--dbt-manifest", type=click.Path(), help="Path to dbt manifest.json")
def detect_orphans(dags: Optional[str], dbt_manifest: Optional[str]):
    """Detect orphaned nodes."""
    # Build graph
    dag_files = []
    if dags:
        dag_path = Path(dags)
        dag_files = list(dag_path.glob("**/*.py"))

    graph = UnifiedGraphBuilder.build_unified_graph(
        dag_files=[str(f) for f in dag_files],
        dbt_manifest=dbt_manifest,
    )

    # Run orphan detection
    engine = DependencyGraphEngine(graph)
    orphans = engine.detect_orphans()

    # Display results
    console.print(
        Panel(
            f"[bold]Orphan Detection Results[/bold]\n"
            f"Sources (no incoming): {len(orphans['sources'])}\n"
            f"Sinks (no outgoing): {len(orphans['sinks'])}\n"
            f"Isolated: {len(orphans['isolated'])}",
            title="Orphan Detection",
        )
    )

    if orphans["isolated"]:
        console.print("\n[bold yellow]Isolated Nodes:[/bold yellow]")
        for node_id in orphans["isolated"][:10]:
            if node_id in graph.nodes:
                console.print(f"  - {graph.nodes[node_id].name}")


@dependency_cli.command()
@click.option("--top", type=int, default=10, help="Show top N nodes")
@click.option("--dags", type=click.Path(), help="Path to DAGs directory")
@click.option("--dbt-manifest", type=click.Path(), help="Path to dbt manifest.json")
def risk_score(top: int, dags: Optional[str], dbt_manifest: Optional[str]):
    """Calculate risk scores for all nodes."""
    # Build graph
    dag_files = []
    if dags:
        dag_path = Path(dags)
        dag_files = list(dag_path.glob("**/*.py"))

    graph = UnifiedGraphBuilder.build_unified_graph(
        dag_files=[str(f) for f in dag_files],
        dbt_manifest=dbt_manifest,
    )

    # Run risk scoring
    engine = RiskScoringEngine(graph)
    scores = engine.score_all_nodes()

    # Sort by risk score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1].risk_score, reverse=True)

    # Display top N
    table = Table(title=f"Top {top} Highest Risk Nodes")
    table.add_column("Node", style="cyan")
    table.add_column("Risk Score", style="red")
    table.add_column("Severity", style="yellow")
    table.add_column("Downstream", style="green")

    for node_id, result in sorted_scores[:top]:
        node = graph.nodes.get(node_id)
        if node:
            table.add_row(
                node.name,
                f"{result.risk_score:.1f}",
                result.severity.value.upper(),
                str(result.metadata.get("downstream_nodes", 0)),
            )

    console.print(table)


def register_dependency_cli(main_cli):
    """Register dependency CLI group with main CLI."""
    main_cli.add_command(dependency_cli, name="dependency")
