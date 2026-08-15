"""Core dependency graph engine with traversal and analysis algorithms."""

import logging
from collections import deque
from typing import Any, Dict, List, Optional, Set

from .models import (
    DependencyGraph,
    NodeType,
)

logger = logging.getLogger(__name__)


class DependencyGraphEngine:
    """Core graph engine with algorithms for traversal and analysis."""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self._upstream_cache: Dict[str, Set[str]] = {}
        self._downstream_cache: Dict[str, Set[str]] = {}
        self._cycles_cache: Optional[List[List[str]]] = None
        self._cache_valid = True

    def invalidate_cache(self):
        """Invalidate all caches after graph modification."""
        self._upstream_cache.clear()
        self._downstream_cache.clear()
        self._cycles_cache = None
        self._cache_valid = False

    # Traversal algorithms

    def get_upstream_nodes(self, node_id: str, max_depth: Optional[int] = None) -> List[str]:
        """
        Get all upstream nodes (dependencies) of a node using BFS.

        Args:
            node_id: The node to analyze
            max_depth: Optional maximum traversal depth

        Returns:
            List of upstream node IDs
        """
        if node_id not in self.graph.nodes:
            return []

        # Check cache
        if node_id in self._upstream_cache and max_depth is None:
            return list(self._upstream_cache[node_id])

        visited = set()
        queue = deque([(node_id, 0)])
        upstream = set()

        while queue:
            current_id, depth = queue.popleft()

            # Check depth limit
            if max_depth is not None and depth >= max_depth:
                continue

            # Get incoming edges (dependencies)
            for edge in self.graph.get_edges_to(current_id):
                source_id = edge.source

                if source_id not in visited:
                    visited.add(source_id)
                    upstream.add(source_id)
                    queue.append((source_id, depth + 1))

        # Cache if no depth limit
        if max_depth is None:
            self._upstream_cache[node_id] = upstream

        return sorted(list(upstream))

    def get_downstream_nodes(self, node_id: str, max_depth: Optional[int] = None) -> List[str]:
        """
        Get all downstream nodes (dependents) of a node using BFS.

        Args:
            node_id: The node to analyze
            max_depth: Optional maximum traversal depth

        Returns:
            List of downstream node IDs
        """
        if node_id not in self.graph.nodes:
            return []

        # Check cache
        if node_id in self._downstream_cache and max_depth is None:
            return list(self._downstream_cache[node_id])

        visited = set()
        queue = deque([(node_id, 0)])
        downstream = set()

        while queue:
            current_id, depth = queue.popleft()

            # Check depth limit
            if max_depth is not None and depth >= max_depth:
                continue

            # Get outgoing edges (dependents)
            for edge in self.graph.get_edges_from(current_id):
                target_id = edge.target

                if target_id not in visited:
                    visited.add(target_id)
                    downstream.add(target_id)
                    queue.append((target_id, depth + 1))

        # Cache if no depth limit
        if max_depth is None:
            self._downstream_cache[node_id] = downstream

        return sorted(list(downstream))

    def get_reach(self, node_id: str) -> Dict[str, int]:
        """
        Get reachability from a node with distances.

        Returns:
            Dict of {node_id: distance}
        """
        if node_id not in self.graph.nodes:
            return {}

        visited = {node_id: 0}
        queue = deque([(node_id, 0)])

        while queue:
            current_id, distance = queue.popleft()

            for edge in self.graph.get_edges_from(current_id):
                target_id = edge.target

                if target_id not in visited:
                    visited[target_id] = distance + 1
                    queue.append((target_id, distance + 1))

        return visited

    def get_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """
        Find shortest path between two nodes using BFS.

        Returns:
            List of node IDs from source to target, or None if no path
        """
        if source_id not in self.graph.nodes or target_id not in self.graph.nodes:
            return None

        if source_id == target_id:
            return [source_id]

        visited = {source_id}
        queue = deque([(source_id, [source_id])])

        while queue:
            current_id, path = queue.popleft()

            for edge in self.graph.get_edges_from(current_id):
                neighbor_id = edge.target

                if neighbor_id == target_id:
                    return path + [neighbor_id]

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None

    # Cycle detection

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect all cycles in the dependency graph using DFS.

        Returns:
            List of cycles, where each cycle is a list of node IDs
        """
        if self._cycles_cache is not None:
            return self._cycles_cache

        cycles = []
        visited = set()
        rec_stack = set()
        path_stack = []

        def dfs(node_id: str):
            visited.add(node_id)
            rec_stack.add(node_id)
            path_stack.append(node_id)

            for edge in self.graph.get_edges_from(node_id):
                neighbor_id = edge.target

                if neighbor_id not in visited:
                    dfs(neighbor_id)
                elif neighbor_id in rec_stack:
                    # Found a cycle
                    cycle_start_idx = path_stack.index(neighbor_id)
                    cycle = path_stack[cycle_start_idx:] + [neighbor_id]
                    cycles.append(cycle)

            path_stack.pop()
            rec_stack.discard(node_id)

        # Run DFS from all unvisited nodes
        for node_id in self.graph.nodes:
            if node_id not in visited:
                dfs(node_id)

        # Cache result
        self._cycles_cache = cycles
        return cycles

    def has_cycle(self) -> bool:
        """Check if graph has any cycles."""
        return len(self.detect_cycles()) > 0

    # Orphan detection

    def detect_orphans(self) -> Dict[str, List[str]]:
        """
        Detect orphaned nodes (no incoming/outgoing edges).

        Returns:
            Dict with 'sources' (no incoming) and 'sinks' (no outgoing)
        """
        sources = []  # No incoming edges
        sinks = []    # No outgoing edges

        for node_id, node in self.graph.nodes.items():
            has_incoming = any(e.target == node_id for e in self.graph.edges)
            has_outgoing = any(e.source == node_id for e in self.graph.edges)

            if not has_incoming:
                sources.append(node_id)
            if not has_outgoing:
                sinks.append(node_id)

        return {
            "sources": sorted(sources),
            "sinks": sorted(sinks),
            "isolated": sorted([n for n in sources if n in sinks]),
        }

    def detect_disconnected_components(self) -> List[Set[str]]:
        """
        Find disconnected components in the graph.

        Returns:
            List of sets, each containing node IDs in one component
        """
        visited = set()
        components = []

        def dfs(node_id: str, component: Set[str]):
            visited.add(node_id)
            component.add(node_id)

            # Check both incoming and outgoing edges
            for edge in self.graph.edges:
                if edge.source == node_id and edge.target not in visited:
                    dfs(edge.target, component)
                elif edge.target == node_id and edge.source not in visited:
                    dfs(edge.source, component)

        for node_id in self.graph.nodes:
            if node_id not in visited:
                component = set()
                dfs(node_id, component)
                components.append(component)

        return components

    # Advanced analysis

    def get_critical_path(self) -> List[str]:
        """
        Find the longest path in the DAG (critical path).
        For cyclic graphs, returns longest acyclic path.
        """
        if self.has_cycle():
            logger.warning("Graph has cycles; returning longest acyclic path")

        max_path = []
        visited = set()

        def dfs(node_id: str, path: List[str]) -> List[str]:
            nonlocal max_path
            visited.add(node_id)

            if len(path) > len(max_path):
                max_path = path[:]

            for edge in self.graph.get_edges_from(node_id):
                if edge.target not in visited:
                    path.append(edge.target)
                    dfs(edge.target, path)
                    path.pop()

            visited.discard(node_id)

        for node_id in self.graph.nodes:
            path = [node_id]
            dfs(node_id, path)

        return max_path

    def get_strongly_connected_components(self) -> List[Set[str]]:
        """
        Find strongly connected components using Tarjan's algorithm.
        For dependency graphs, identifies circular dependencies.
        """
        index = 0
        stack = []
        indices = {}
        lowlinks = {}
        on_stack = set()
        sccs = []

        def strongconnect(node_id: str):
            nonlocal index
            indices[node_id] = index
            lowlinks[node_id] = index
            index += 1
            stack.append(node_id)
            on_stack.add(node_id)

            for edge in self.graph.get_edges_from(node_id):
                target_id = edge.target
                if target_id not in indices:
                    strongconnect(target_id)
                    lowlinks[node_id] = min(lowlinks[node_id], lowlinks[target_id])
                elif target_id in on_stack:
                    lowlinks[node_id] = min(lowlinks[node_id], indices[target_id])

            if lowlinks[node_id] == indices[node_id]:
                scc = set()
                while True:
                    node = stack.pop()
                    on_stack.discard(node)
                    scc.add(node)
                    if node == node_id:
                        break
                sccs.append(scc)

        for node_id in self.graph.nodes:
            if node_id not in indices:
                strongconnect(node_id)

        return sccs

    def get_node_centrality(self) -> Dict[str, float]:
        """
        Calculate degree centrality for each node.

        Returns:
            Dict of {node_id: centrality_score}
        """
        max_degree = len(self.graph.nodes) - 1
        if max_degree == 0:
            return {n: 0.0 for n in self.graph.nodes}

        centrality = {}
        for node_id in self.graph.nodes:
            upstream = len(self.get_upstream_nodes(node_id))
            downstream = len(self.get_downstream_nodes(node_id))
            total_degree = upstream + downstream
            centrality[node_id] = total_degree / (2 * max_degree)

        return centrality

    def filter_by_type(self, node_type: NodeType) -> List[str]:
        """Get all nodes of a specific type."""
        return [n.id for n in self.graph.nodes.values() if n.type == node_type]

    def filter_by_owner(self, owner: str) -> List[str]:
        """Get all nodes owned by a specific owner."""
        return [n.id for n in self.graph.nodes.values() if n.owner == owner]

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        cycles = self.detect_cycles()
        orphans = self.detect_orphans()
        components = self.detect_disconnected_components()
        centrality = self.get_node_centrality()

        return {
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "cycle_count": len(cycles),
            "has_cycles": len(cycles) > 0,
            "component_count": len(components),
            "is_connected": len(components) <= 1,
            "orphaned_sources": len(orphans["sources"]),
            "orphaned_sinks": len(orphans["sinks"]),
            "orphaned_isolated": len(orphans["isolated"]),
            "average_degree": sum(len(self.get_upstream_nodes(n)) + len(self.get_downstream_nodes(n))
                                 for n in self.graph.nodes) / len(self.graph.nodes) if self.graph.nodes else 0,
            "avg_centrality": sum(centrality.values()) / len(centrality) if centrality else 0,
            "max_centrality": max(centrality.values()) if centrality else 0,
            "node_types": self.graph.get_node_count_by_type(),
        }
