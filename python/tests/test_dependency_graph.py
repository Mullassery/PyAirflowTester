"""Tests for dependency graph engine."""

import pytest
from pyairflowtester.dependency_intelligence.cache import TieredCache
from pyairflowtester.dependency_intelligence.graph import DependencyGraphEngine
from pyairflowtester.dependency_intelligence.models import (
    DependencyGraph,
    Edge,
    Node,
    NodeSeverity,
    NodeType,
)


@pytest.fixture
def simple_graph():
    """Create a simple test graph."""
    graph = DependencyGraph()

    # Create nodes
    nodes = {
        "task_1": Node("task_1", "Task 1", NodeType.TASK, severity=NodeSeverity.CRITICAL),
        "task_2": Node("task_2", "Task 2", NodeType.TASK),
        "task_3": Node("task_3", "Task 3", NodeType.TASK),
        "task_4": Node("task_4", "Task 4", NodeType.TASK),
    }

    for node in nodes.values():
        graph.add_node(node)

    # Create edges: 1 -> 2 -> 3, 1 -> 4
    graph.add_edge(Edge("task_1", "task_2"))
    graph.add_edge(Edge("task_2", "task_3"))
    graph.add_edge(Edge("task_1", "task_4"))

    return graph


@pytest.fixture
def cyclic_graph():
    """Create a graph with cycles."""
    graph = DependencyGraph()

    nodes = {
        "a": Node("a", "A", NodeType.TASK),
        "b": Node("b", "B", NodeType.TASK),
        "c": Node("c", "C", NodeType.TASK),
    }

    for node in nodes.values():
        graph.add_node(node)

    # Create cycle: a -> b -> c -> a
    graph.add_edge(Edge("a", "b"))
    graph.add_edge(Edge("b", "c"))
    graph.add_edge(Edge("c", "a"))

    return graph


class TestTraversal:
    """Test graph traversal algorithms."""

    def test_upstream_traversal(self, simple_graph):
        """Test getting upstream nodes."""
        engine = DependencyGraphEngine(simple_graph)

        upstream_of_3 = engine.get_upstream_nodes("task_3")
        assert "task_2" in upstream_of_3
        assert "task_1" in upstream_of_3
        assert len(upstream_of_3) == 2

    def test_downstream_traversal(self, simple_graph):
        """Test getting downstream nodes."""
        engine = DependencyGraphEngine(simple_graph)

        downstream_of_1 = engine.get_downstream_nodes("task_1")
        assert "task_2" in downstream_of_1
        assert "task_3" in downstream_of_1
        assert "task_4" in downstream_of_1
        assert len(downstream_of_1) == 3

    def test_upstream_with_depth(self, simple_graph):
        """Test upstream traversal with depth limit."""
        engine = DependencyGraphEngine(simple_graph)

        upstream_depth_1 = engine.get_upstream_nodes("task_3", max_depth=1)
        assert upstream_depth_1 == ["task_2"]

    def test_nonexistent_node(self, simple_graph):
        """Test traversal of nonexistent node."""
        engine = DependencyGraphEngine(simple_graph)

        assert engine.get_upstream_nodes("nonexistent") == []
        assert engine.get_downstream_nodes("nonexistent") == []

    def test_reachability(self, simple_graph):
        """Test reachability from a node."""
        engine = DependencyGraphEngine(simple_graph)

        reach = engine.get_reach("task_1")
        assert reach["task_1"] == 0
        assert reach["task_2"] == 1
        assert reach["task_3"] == 2
        assert reach["task_4"] == 1

    def test_path_finding(self, simple_graph):
        """Test finding shortest path."""
        engine = DependencyGraphEngine(simple_graph)

        path = engine.get_path("task_1", "task_3")
        assert path == ["task_1", "task_2", "task_3"]

        # No path between 3 and 1
        no_path = engine.get_path("task_3", "task_1")
        assert no_path is None


class TestCycleDetection:
    """Test cycle detection algorithms."""

    def test_no_cycles(self, simple_graph):
        """Test graph without cycles."""
        engine = DependencyGraphEngine(simple_graph)

        cycles = engine.detect_cycles()
        assert len(cycles) == 0
        assert not engine.has_cycle()

    def test_simple_cycle(self, cyclic_graph):
        """Test detection of simple cycle."""
        engine = DependencyGraphEngine(cyclic_graph)

        cycles = engine.detect_cycles()
        assert len(cycles) > 0
        assert engine.has_cycle()

        # Check that cycle contains all nodes
        cycle = cycles[0]
        assert len(cycle) == 4  # a -> b -> c -> a (plus the return to a)

    def test_multiple_cycles(self):
        """Test graph with multiple cycles."""
        graph = DependencyGraph()

        nodes = {
            "a": Node("a", "A", NodeType.TASK),
            "b": Node("b", "B", NodeType.TASK),
            "c": Node("c", "C", NodeType.TASK),
        }

        for node in nodes.values():
            graph.add_node(node)

        # Two separate cycles: a -> b -> a and b -> c -> b
        graph.add_edge(Edge("a", "b"))
        graph.add_edge(Edge("b", "a"))
        graph.add_edge(Edge("b", "c"))
        graph.add_edge(Edge("c", "b"))

        engine = DependencyGraphEngine(graph)
        cycles = engine.detect_cycles()
        assert len(cycles) >= 2


class TestOrphanDetection:
    """Test orphan node detection."""

    def test_orphan_detection(self, simple_graph):
        """Test detection of orphaned nodes."""
        engine = DependencyGraphEngine(simple_graph)

        orphans = engine.detect_orphans()
        assert "task_1" in orphans["sources"]  # No incoming edges
        assert "task_3" in orphans["sinks"]  # No outgoing edges
        assert "task_4" in orphans["sinks"]  # No outgoing edges

    def test_isolated_node(self):
        """Test detection of isolated nodes."""
        graph = DependencyGraph()

        nodes = {
            "isolated": Node("isolated", "Isolated", NodeType.TASK),
            "connected": Node("connected", "Connected", NodeType.TASK),
        }

        for node in nodes.values():
            graph.add_node(node)

        # Only one edge
        graph.add_edge(Edge("connected", "connected"))

        engine = DependencyGraphEngine(graph)
        orphans = engine.detect_orphans()

        assert "isolated" in orphans["isolated"]


class TestConnectivityAnalysis:
    """Test connectivity and component analysis."""

    def test_connected_components(self, simple_graph):
        """Test finding connected components."""
        engine = DependencyGraphEngine(simple_graph)

        components = engine.detect_disconnected_components()
        # Simple graph should be mostly connected
        assert len(components) >= 1

    def test_centrality(self, simple_graph):
        """Test node centrality calculation."""
        engine = DependencyGraphEngine(simple_graph)

        centrality = engine.get_node_centrality()
        # task_1 should have high centrality
        assert "task_1" in centrality
        assert centrality["task_1"] > 0

    def test_critical_path(self, simple_graph):
        """Test critical path finding."""
        engine = DependencyGraphEngine(simple_graph)

        path = engine.get_critical_path()
        assert len(path) > 0
        # Should be task_1 -> task_2 -> task_3 (longest path)
        assert path[0] == "task_1"


class TestGraphStats:
    """Test graph statistics."""

    def test_stats(self, simple_graph):
        """Test graph statistics calculation."""
        engine = DependencyGraphEngine(simple_graph)

        stats = engine.get_stats()
        assert stats["node_count"] == 4
        assert stats["edge_count"] == 3
        assert not stats["has_cycles"]
        assert stats["component_count"] >= 1

    def test_node_type_filtering(self, simple_graph):
        """Test filtering nodes by type."""
        engine = DependencyGraphEngine(simple_graph)

        task_nodes = engine.filter_by_type(NodeType.TASK)
        assert len(task_nodes) == 4

    def test_node_owner_filtering(self):
        """Test filtering nodes by owner."""
        graph = DependencyGraph()

        nodes = {
            "team_a_task": Node("team_a_task", "Task A", NodeType.TASK, owner="team_a"),
            "team_b_task": Node("team_b_task", "Task B", NodeType.TASK, owner="team_b"),
        }

        for node in nodes.values():
            graph.add_node(node)

        engine = DependencyGraphEngine(graph)

        team_a_nodes = engine.filter_by_owner("team_a")
        assert len(team_a_nodes) == 1
        assert "team_a_task" in team_a_nodes


class TestCaching:
    """Test caching behavior."""

    def test_cache_invalidation(self, simple_graph):
        """Test that cache is invalidated on graph changes."""
        engine = DependencyGraphEngine(simple_graph)

        # Populate cache
        upstream_1 = engine.get_upstream_nodes("task_3")
        assert len(upstream_1) == 2

        # Add a new edge
        new_node = Node("task_5", "Task 5", NodeType.TASK)
        simple_graph.add_node(new_node)
        simple_graph.add_edge(Edge("task_3", "task_5"))

        # Invalidate cache
        engine.invalidate_cache()

        # Results should still be computed (but from scratch)
        upstream_3_after = engine.get_upstream_nodes("task_3")
        assert len(upstream_3_after) == 2


class TestTieredCacheIntegration:
    """DependencyGraphEngine's optional TieredCache param (cache.py) --
    unlike the in-process-only cache above, this can survive across
    separate DependencyGraphEngine instances (e.g. separate process
    invocations, with an L3 SqliteCache)."""

    def test_engine_without_cache_still_works(self, cyclic_graph):
        engine = DependencyGraphEngine(cyclic_graph)
        assert engine.cache is None
        assert len(engine.detect_cycles()) > 0

    def test_detect_cycles_populates_and_reuses_cache(self, cyclic_graph):
        cache = TieredCache()
        engine = DependencyGraphEngine(cyclic_graph, cache=cache)

        cycles = engine.detect_cycles()
        assert len(cycles) > 0

        cache_key = f"cycles:{engine._graph_content_hash()}"
        assert cache.get(cache_key) == cycles

    def test_second_engine_instance_reuses_first_ones_cached_result(self, cyclic_graph):
        """This is the actual cross-invocation persistence the roadmap asked
        for: a fresh DependencyGraphEngine over the *same* graph content
        gets a cache hit from a previous engine's work."""
        cache = TieredCache()
        first_engine = DependencyGraphEngine(cyclic_graph, cache=cache)
        first_cycles = first_engine.detect_cycles()

        second_engine = DependencyGraphEngine(cyclic_graph, cache=cache)
        second_cycles = second_engine.detect_cycles()

        assert second_cycles == first_cycles
        # Confirm it was actually a cache hit, not recomputed identically by chance.
        assert cache.l1.stats.hits >= 1

    def test_changed_graph_gets_a_different_cache_key_not_stale_results(self, simple_graph):
        cache = TieredCache()
        engine = DependencyGraphEngine(simple_graph, cache=cache)
        hash_before = engine._graph_content_hash()
        engine.detect_cycles()

        simple_graph.add_node(Node("task_5", "Task 5", NodeType.TASK))
        simple_graph.add_edge(Edge("task_3", "task_5"))

        hash_after = engine._graph_content_hash()
        assert hash_after != hash_before

    def test_strongly_connected_components_cache_round_trips_as_sets(self, cyclic_graph):
        cache = TieredCache()
        engine = DependencyGraphEngine(cyclic_graph, cache=cache)

        first = engine.get_strongly_connected_components()
        second_engine = DependencyGraphEngine(cyclic_graph, cache=cache)
        second = second_engine.get_strongly_connected_components()

        assert first == second
        assert all(isinstance(scc, set) for scc in second)

    def test_sqlite_backed_cache_persists_across_process_boundary_simulation(
        self, cyclic_graph, tmp_path
    ):
        from pyairflowtester.dependency_intelligence.cache import SqliteCache

        db_path = tmp_path / "graph_cache.db"

        # Simulate one process run.
        cache1 = TieredCache(l3=SqliteCache(db_path))
        engine1 = DependencyGraphEngine(cyclic_graph, cache=cache1)
        cycles1 = engine1.detect_cycles()
        cache1.l3.close()

        # Simulate a second, independent process run against a fresh L1.
        cache2 = TieredCache(l3=SqliteCache(db_path))
        engine2 = DependencyGraphEngine(cyclic_graph, cache=cache2)
        cycles2 = engine2.detect_cycles()

        assert cycles2 == cycles1
        cache2.l3.close()
