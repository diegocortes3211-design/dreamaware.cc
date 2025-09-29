#!/usr/bin/env bash
# scripts/ensure_gnn.sh
set -euo pipefail

# Ensure file exists with a recognizable placeholder for Jules to patch
if [ ! -f services/secfold/gnn_train.py ]; then
    mkdir -p services/secfold
    cat > services/secfold/gnn_train.py <<'PY'
from __future__ import annotations
import torch

# Minimal stub so Jules can patch the feature line below:
def train_gnn():
    # Placeholder so tools/jules/tasks.yaml can replace torch.rand(...) with build_node_features(...)
    x = torch.rand(10, 8) # <<< Jules will patch this line
    print("GNN stub OK; tensor shape:", tuple(x.shape))

if __name__ == "__main__":
    train_gnn()
PY
    echo "[+] Wrote minimal services/secfold/gnn_train.py stub."
else
    echo "[=] Found services/secfold/gnn_train.py"
fi

# Make sure repo has a tests dir (optional)
mkdir -p tests/secfold