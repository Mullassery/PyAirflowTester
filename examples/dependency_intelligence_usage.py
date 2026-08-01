"""Example usage of PyAirflowTester Dependency Intelligence Engine."""

from pyairflowtester.dependency_intelligence import (
    UnifiedGraphBuilder,
    DependencyGraphEngine,
    ImpactAnalysisEngine,
    BlastRadiusEngine,
    RiskScoringEngine,
    DriftDetectionEngine,
    NodeSeverity,
    NodeType,
)


def example_1_build_graph():
    """Example 1: Build a dependency graph from Airflow DAGs and dbt manifest."""
    print("=" * 60)
    print("Example 1: Building Dependency Graph")
    print("=" * 60)

    # Build unified graph from multiple sources
    graph = UnifiedGraphBuilder.build_unified_graph(
        dag_files=[
            "dags/etl/extract.py",
            "dags/etl/transform.py",
            "dags/reporting/reports.py",
        ],
        dbt_manifest="dbt/target/manifest.json",
        dataset_files=["dags/datasets/"],
    )

    # Display graph statistics
    stats = graph.stats()
    print(f"\nGraph Statistics:")
    print(f"  Total Nodes: {stats['node_count']}")
    print(f"  Total Edges: {stats['edge_count']}")
    print(f"  Critical Nodes: {stats['critical_nodes']}")
    print(f"  Version: {stats['version']}")

    # Display node type breakdown
    print(f"\nNode Types:")
    for node_type, count in stats['node_types'].items():
        print(f"  {node_type.value}: {count}")

    return graph


def example_2_impact_analysis(graph):
    """Example 2: Analyze the impact of changing a specific node."""
    print("\n" + "=" * 60)
    print("Example 2: Impact Analysis")
    print("=" * 60)

    # Create impact analysis engine
    impact_engine = ImpactAnalysisEngine(graph)

    # Analyze impact of changing the 'raw_orders' DAG
    print("\nAnalyzing impact of changing 'dag_raw_orders'...")
    result = impact_engine.analyze("dag_raw_orders", max_depth=10)

    print(f"\nImpact Analysis Results:")
    print(f"  Impacted Nodes: {len(result.impacted_nodes)}")
    print(f"  Max Impact Depth: {result.impact_depth}")
    print(f"  Impact Score: {result.impact_score:.2%}")

    # Show breakdown by severity
    print(f"\nImpacted Nodes by Severity:")
    for severity in [NodeSeverity.CRITICAL, NodeSeverity.HIGH,
                     NodeSeverity.MEDIUM, NodeSeverity.LOW]:
        nodes = result.by_severity.get(severity, [])
        if nodes:
            print(f"  {severity.value.upper()}: {len(nodes)} nodes")
            # Show first 3
            for node_id in nodes[:3]:
                node = graph.nodes.get(node_id)
                if node:
                    print(f"    - {node.name}")

    # Show breakdown by type
    print(f"\nImpacted Nodes by Type:")
    for node_type in [NodeType.DAG, NodeType.TASK, NodeType.DBT_MODEL]:
        nodes = result.by_type.get(node_type, [])
        if nodes:
            print(f"  {node_type.value}: {len(nodes)} nodes")

    return result


def example_3_blast_radius(graph):
    """Example 3: Calculate blast radius of deploying changes."""
    print("\n" + "=" * 60)
    print("Example 3: Blast Radius Analysis")
    print("=" * 60)

    # Create blast radius engine
    blast_engine = BlastRadiusEngine(graph)

    # Scenario: We're deploying changes to multiple models
    changed_nodes = ["model_users", "model_orders"]
    print(f"\nAnalyzing blast radius for changes to: {changed_nodes}")

    result = blast_engine.analyze(changed_nodes)

    print(f"\nBlast Radius Results:")
    print(f"  Changed Nodes: {len(result.change_nodes)}")
    print(f"  Affected Nodes: {result.blast_radius}")
    print(f"  Blast Depth: {result.blast_depth}")
    print(f"  Risk Level: {result.risk_level.upper()}")
    print(f"  Safe to Deploy: {'✓ YES' if result.deployable else '✗ NO'}")

    # Show severity distribution
    print(f"\nSeverity Distribution of Affected Nodes:")
    for severity, count in sorted(result.severity_distribution.items(),
                                  key=lambda x: x[0].value, reverse=True):
        print(f"  {severity.value.upper()}: {count}")

    # Recommendation
    if not result.deployable:
        print(f"\n⚠ WARNING: High-risk deployment!")
        print(f"  Recommendation: Review affected critical/high nodes")
        print(f"  Risk factors: {result.risk_level} impact across {result.blast_radius} nodes")
    else:
        print(f"\n✓ APPROVED: Safe to deploy")

    return result


def example_4_cycle_detection(graph):
    """Example 4: Detect circular dependencies."""
    print("\n" + "=" * 60)
    print("Example 4: Cycle Detection")
    print("=" * 60)

    # Create graph engine
    engine = DependencyGraphEngine(graph)

    # Detect cycles
    cycles = engine.detect_cycles()

    if cycles:
        print(f"\n⚠ Found {len(cycles)} circular dependencies!")

        for i, cycle in enumerate(cycles, 1):
            print(f"\nCycle {i}:")
            cycle_path = " → ".join([
                graph.nodes.get(n, type('', (), {'name': n})()).name
                for n in cycle
            ])
            print(f"  {cycle_path}")
    else:
        print(f"\n✓ No circular dependencies found!")

    return cycles


def example_5_orphan_detection(graph):
    """Example 5: Detect orphaned nodes."""
    print("\n" + "=" * 60)
    print("Example 5: Orphan Detection")
    print("=" * 60)

    # Create graph engine
    engine = DependencyGraphEngine(graph)

    # Detect orphans
    orphans = engine.detect_orphans()

    print(f"\nOrphan Detection Results:")
    print(f"  Sources (no incoming): {len(orphans['sources'])}")
    print(f"  Sinks (no outgoing): {len(orphans['sinks'])}")
    print(f"  Isolated: {len(orphans['isolated'])}")

    if orphans['isolated']:
        print(f"\nIsolated Nodes:")
        for node_id in orphans['isolated'][:10]:
            node = graph.nodes.get(node_id)
            if node:
                print(f"  - {node.name} ({node.type.value})")

    return orphans


def example_6_risk_scoring(graph):
    """Example 6: Calculate risk scores for all nodes."""
    print("\n" + "=" * 60)
    print("Example 6: Risk Scoring")
    print("=" * 60)

    # Create risk scoring engine
    risk_engine = RiskScoringEngine(graph)

    # Score all nodes
    print("\nCalculating risk scores for all nodes...")
    all_scores = risk_engine.score_all_nodes()

    # Sort by score
    sorted_scores = sorted(
        all_scores.items(),
        key=lambda x: x[1].risk_score,
        reverse=True
    )

    # Show top 10 highest risk nodes
    print(f"\nTop 10 Highest Risk Nodes:")
    print(f"{'Node':<25} {'Score':<8} {'Severity':<12} {'Factors':<30}")
    print("-" * 75)

    for node_id, result in sorted_scores[:10]:
        node = graph.nodes.get(node_id)
        if node:
            factors_str = ", ".join(result.factors[:2]) if result.factors else "N/A"
            if len(result.factors) > 2:
                factors_str += f", +{len(result.factors)-2} more"

            print(f"{node.name:<25} {result.risk_score:<8.1f} "
                  f"{result.severity.value:<12} {factors_str:<30}")

    # Show risk distribution
    print(f"\nRisk Score Distribution:")
    critical_count = sum(1 for r in all_scores if r[1].risk_score >= 8.0)
    high_count = sum(1 for r in all_scores if 6.0 <= r[1].risk_score < 8.0)
    medium_count = sum(1 for r in all_scores if 3.0 <= r[1].risk_score < 6.0)
    low_count = sum(1 for r in all_scores if r[1].risk_score < 3.0)

    print(f"  Critical (8.0+): {critical_count}")
    print(f"  High (6.0-8.0): {high_count}")
    print(f"  Medium (3.0-6.0): {medium_count}")
    print(f"  Low (<3.0): {low_count}")

    return all_scores


def example_7_drift_detection(current_graph, previous_version_graph=None):
    """Example 7: Detect dependency drift (changes)."""
    print("\n" + "=" * 60)
    print("Example 7: Drift Detection")
    print("=" * 60)

    # If no previous graph provided, use current as baseline
    if previous_version_graph is None:
        from pyairflowtester.dependency_intelligence.models import DependencyGraph
        previous_version_graph = DependencyGraph()

    # Create drift detection engine
    drift_engine = DriftDetectionEngine(current_graph, previous_version_graph)

    # Detect drift
    result = drift_engine.detect_drift()

    print(f"\nDrift Detection Results:")
    print(f"  Drifts Detected: {result.drift_count}")
    print(f"  Affected Nodes: {len(result.affected_nodes)}")
    print(f"  Severity: {result.severity.value}")

    if result.detected_drifts:
        print(f"\nChanges Detected:")
        for drift in result.detected_drifts:
            print(f"  - {drift['type']}: {drift.get('count', '?')} changes")

        print(f"\nDetails:")
        for detail in result.details:
            print(f"  - {detail}")
    else:
        print(f"\n✓ No drift detected (graphs are identical)")

    return result


def example_8_advanced_queries(graph):
    """Example 8: Advanced graph queries."""
    print("\n" + "=" * 60)
    print("Example 8: Advanced Queries")
    print("=" * 60)

    engine = DependencyGraphEngine(graph)

    # Query 1: Find upstream critical dependencies
    print("\nQuery 1: Upstream dependencies of 'model_orders'")
    upstream = engine.get_upstream_nodes("model_orders", max_depth=3)
    print(f"  Found {len(upstream)} upstream nodes (depth 3)")

    # Query 2: Shortest path between two nodes
    print("\nQuery 2: Dependency path from 'dag_raw' to 'dashboard_sales'")
    path = engine.get_path("dag_raw", "dashboard_sales")
    if path:
        path_str = " → ".join([
            graph.nodes.get(n, type('', (), {'name': n})()).name
            for n in path
        ])
        print(f"  Path: {path_str}")
    else:
        print(f"  No path found (nodes are disconnected)")

    # Query 3: Get nodes by owner
    print("\nQuery 3: Nodes owned by 'data-team'")
    owned_nodes = engine.filter_by_owner("data-team")
    print(f"  Found {len(owned_nodes)} nodes")

    # Query 4: Get nodes by type
    print("\nQuery 4: All dbt models")
    dbt_models = engine.filter_by_type(NodeType.DBT_MODEL)
    print(f"  Found {len(dbt_models)} dbt models")

    # Query 5: Critical path analysis
    print("\nQuery 5: Critical path (longest dependency chain)")
    critical_path = engine.get_critical_path()
    if critical_path:
        path_str = " → ".join([
            graph.nodes.get(n, type('', (), {'name': n})()).name
            for n in critical_path[:5]
        ])
        print(f"  Longest path ({len(critical_path)} nodes): {path_str}...")

    # Query 6: Centrality analysis
    print("\nQuery 6: Most central nodes")
    centrality = engine.get_node_centrality()
    top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    for node_id, score in top_central:
        node = graph.nodes.get(node_id)
        if node:
            print(f"  {node.name}: {score:.2%}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PyAirflowTester Dependency Intelligence - Usage Examples")
    print("=" * 60)

    # Example 1: Build graph
    graph = example_1_build_graph()

    # Example 2: Impact analysis
    example_2_impact_analysis(graph)

    # Example 3: Blast radius
    example_3_blast_radius(graph)

    # Example 4: Cycle detection
    example_4_cycle_detection(graph)

    # Example 5: Orphan detection
    example_5_orphan_detection(graph)

    # Example 6: Risk scoring
    example_6_risk_scoring(graph)

    # Example 7: Drift detection
    example_7_drift_detection(graph)

    # Example 8: Advanced queries
    example_8_advanced_queries(graph)

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
