from __future__ import annotations
from collections import deque
from typing import Dict, List, Set

class PathPredictor:
    """
    Predicts potential attack paths through the codebase graph.
    """

    def __init__(self, graph: Dict[str, List[str]]):
        self.graph = graph

    def predict_paths(self, vulnerability_nodes: List[str]) -> Dict[str, List[str]]:
        """
        Finds all reachable nodes from a given set of vulnerability nodes.

        Args:
            vulnerability_nodes: A list of file paths identified as vulnerable.

        Returns:
            A dictionary where keys are vulnerability nodes and values are lists of
            reachable file paths (potential attack paths).
        """
        all_predicted_paths: Dict[str, List[str]] = {}

        for start_node in vulnerability_nodes:
            if start_node not in self.graph:
                # If the vulnerable node is not in the graph (e.g., not a Python file), skip it.
                all_predicted_paths[start_node] = []
                continue

            # Use BFS to find all reachable nodes
            queue = deque([start_node])
            visited: Set[str] = {start_node}

            while queue:
                current_node = queue.popleft()

                # The neighbors in our graph are the nodes that the current_node *depends on*.
                # For attack path analysis, we want to see what *depends on* the current_node.
                # So we need to traverse the graph in reverse.
                for node, dependencies in self.graph.items():
                    if current_node in dependencies and node not in visited:
                        visited.add(node)
                        queue.append(node)

            # The path is the set of all visited nodes, excluding the start node itself.
            path = sorted(list(visited - {start_node}))
            all_predicted_paths[start_node] = path

        return all_predicted_paths