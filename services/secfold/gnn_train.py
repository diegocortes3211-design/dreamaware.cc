from __future__ import annotations
import torch
from typing import List, Dict, Any

def build_node_features(sequence: List[Any], node_map: Dict[Any, Any]) -> torch.Tensor:
    """
    Placeholder for the real feature builder.
    In a real scenario, this would generate meaningful features.
    """
    print("--> build_node_features: Using placeholder implementation.")
    # Return a random tensor with a shape derived from the inputs
    num_nodes = len(node_map)
    feature_dim = 8  # Matching the original dummy data
    return torch.rand(num_nodes, feature_dim)

def train_gnn():
    """
    This function now simulates a context for the patched code to execute.
    """
    # Mock a 'seq' and 'self' object to match the patched function call
    seq = [None, None, None]  # A dummy sequence of objects

    class MockContext:
        """A mock class to hold the node_map attribute."""
        def __init__(self):
            self.node_map = {"node1": 0, "node2": 1, "node3": 2}

    mock_self = MockContext()

    # The patcher replaces `torch.rand(...)` with the following line.
    # By defining the function and mock context, we prevent a NameError.
    x = build_node_features(seq[:-1], mock_self.node_map)

    print("GNN stub OK; tensor shape:", tuple(x.shape))

if __name__ == "__main__":
    train_gnn()