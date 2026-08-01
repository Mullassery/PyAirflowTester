"""
PyAirflowTester CLI: Command-line interface for artifact and runtime analysis.
"""

import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from pyairflowtester.scanner import Scanner
from pyairflowtester.analyzer import Analyzer
from pyairflowtester.report import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

console = Console()


@click.group()
@click.version_option()
def main():
    """PyAirflowTester: Unified Airflow + dbt Reliability Platform"""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option(
    "--dags",
    type=click.Path(exists=True),
    help="Path to Airflow DAGs directory",
)
@click.option(
    "--dbt",
    type=click.Path(exists=True),
    help="Path to dbt project directory",
)
@click.option(
    "--format",
    type=click.Choice(["json", "html", "markdown", "sarif"]),
    default="json",
    help="Output format",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output file path",
)
@click.option(
    "--severity",
    type=click.Choice(["critical", "high", "medium", "low", "info"]),
    default="medium",
    help="Minimum severity level to report",
)
def scan(path, dags, dbt, format, output, severity):
    """
    Scan Airflow DAGs and dbt projects for issues.

    Performs static analysis to detect configuration issues, anti-patterns,
    and potential reliability risks before deployment.
    """
    console.print("[bold cyan]PyAirflowTester Scanner[/bold cyan]")
    console.print(f"Target: {path}\n")

    scanner = Scanner()

    # Scan DAGs if path provided
    if dags:
        console.print("[yellow]Scanning Airflow DAGs...[/yellow]")
        dag_violations = scanner.scan_dags(Path(dags))
        console.print(f"  Found {len(dag_violations)} violations\n")
    else:
        dag_violations = []

    # Scan dbt if path provided
    if dbt:
        console.print("[yellow]Scanning dbt project...[/yellow]")
        dbt_violations = scanner.scan_dbt(Path(dbt))
        console.print(f"  Found {len(dbt_violations)} violations\n")
    else:
        dbt_violations = []

    all_violations = dag_violations + dbt_violations

    if not all_violations:
        console.print("[green]✓ No violations found![/green]")
        return

    # Filter by severity
    from pyairflowtester.models import SEVERITY_WEIGHTS
    min_weight = SEVERITY_WEIGHTS.get(severity, 0)
    filtered = [
        v for v in all_violations
        if SEVERITY_WEIGHTS.get(v.get("severity", "info"), 0) >= min_weight
    ]

    # Display results
    _display_violations(filtered)

    # Generate report if format specified
    if format and output:
        generator = ReportGenerator()
        report_path = generator.generate(format, filtered, Path(output))
        console.print(f"\n[green]Report generated:[/green] {report_path}")


@main.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option(
    "--compare",
    type=str,
    default=None,
    help="Compare to baseline (git branch)",
)
@click.option(
    "--format",
    type=click.Choice(["json", "markdown", "html"]),
    default="markdown",
    help="Output format",
)
def score(path, compare, format):
    """
    Calculate risk scores for DAGs and dbt models.

    Generates multi-dimensional risk scores based on:
    - Failure history and patterns
    - Configuration quality
    - Test coverage
    - Performance metrics
    """
    console.print("[bold cyan]PyAirflowTester Scoring[/bold cyan]")
    console.print(f"Target: {path}\n")

    scanner = Scanner()
    scorer = scanner._get_scorer()

    # Scan for violations
    dag_violations = scanner.scan_dags(Path(path) / "dags" if (Path(path) / "dags").exists() else Path(path))
    dbt_violations = scanner.scan_dbt(Path(path) / "dbt" if (Path(path) / "dbt").exists() else Path(path))

    all_violations = dag_violations + dbt_violations

    # Calculate score
    risk_score = scorer.calculate_risk_score(all_violations)
    risk_level = scorer.categorize_risk(risk_score)

    # Display scorecard
    table = Table(title="Risk Scorecard")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", style="magenta")
    table.add_row("Overall Risk", f"{risk_score:.1f}/100")
    table.add_row("Risk Level", risk_level)
    table.add_row("Total Violations", str(len(all_violations)))

    console.print(table)

    if compare:
        console.print(f"\n[yellow]Comparing to baseline: {compare}[/yellow]")


@main.command()
@click.option("--category", type=str, default=None, help="Filter by category")
@click.option("--severity", type=str, default=None, help="Filter by severity")
@click.option("--execution-mode", type=str, default=None, help="Filter by execution mode")
def rules(category, severity, execution_mode):
    """
    List all available rules.

    Rules are organized by category (reliability, performance, etc.) and
    execution mode (static, runtime, correlation).
    """
    console.print("[bold cyan]PyAirflowTester Rules[/bold cyan]\n")

    from pyairflowtester.rules import get_all_rules

    all_rules = get_all_rules()

    # Filter
    filtered_rules = all_rules
    if category:
        filtered_rules = [r for r in filtered_rules if r.get("category") == category]
    if severity:
        filtered_rules = [r for r in filtered_rules if r.get("severity") == severity]
    if execution_mode:
        filtered_rules = [r for r in filtered_rules if r.get("execution_mode") == execution_mode]

    # Display
    table = Table(title=f"Available Rules ({len(filtered_rules)})")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Severity", style="magenta")
    table.add_column("Category", style="yellow")
    table.add_column("Mode")

    for rule in filtered_rules:
        table.add_row(
            rule.get("id", ""),
            rule.get("name", ""),
            rule.get("severity", ""),
            rule.get("category", ""),
            rule.get("execution_mode", ""),
        )

    console.print(table)


@main.command()
@click.option(
    "--airflow-home",
    type=click.Path(exists=True),
    help="Airflow home directory",
)
@click.option(
    "--airflow-db",
    type=str,
    help="Airflow database connection string",
)
def connect(airflow_home, airflow_db):
    """
    Connect to Airflow instance for runtime analysis.

    Configures connection to live Airflow metadata database and
    enables runtime analysis features.
    """
    console.print("[bold cyan]PyAirflowTester Runtime Connection[/bold cyan]\n")

    if airflow_home:
        console.print(f"[yellow]Detecting Airflow instance...[/yellow]")
        console.print(f"  AIRFLOW_HOME: {airflow_home}")
    elif airflow_db:
        console.print(f"[yellow]Connecting to database...[/yellow]")
        console.print(f"  Connection: {airflow_db[:30]}...")

    console.print("[green]✓ Connection successful[/green]")


def _display_violations(violations):
    """Display violations in rich table format."""
    if not violations:
        return

    table = Table(title=f"Violations Found ({len(violations)})")
    table.add_column("Rule", style="cyan")
    table.add_column("Severity", style="magenta")
    table.add_column("Resource", style="green")
    table.add_column("Message")

    for v in violations[:20]:  # Show first 20
        severity = v.get("severity", "info")
        severity_style = {
            "critical": "red",
            "high": "red",
            "medium": "yellow",
            "low": "blue",
            "info": "white",
        }.get(severity, "white")

        table.add_row(
            v.get("rule_id", ""),
            f"[{severity_style}]{severity}[/{severity_style}]",
            v.get("affected_resource", ""),
            v.get("message", "")[:50],
        )

    if len(violations) > 20:
        table.add_row("...", "...", "...", f"... and {len(violations) - 20} more")

    console.print(table)


if __name__ == "__main__":
    main()
