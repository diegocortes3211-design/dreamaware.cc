from __future__ import annotations
import pytest
from pathlib import Path

from services.secfold.graph_builder import GraphBuilder
from services.secfold.path_predictor import PathPredictor

@pytest.fixture
def mock_project(tmp_path: Path) -> Path:
    """Creates a mock project structure for testing."""
    (tmp_path / "main.py").write_text("import utils.helpers\nfrom models.user import User")
    (tmp_path / "utils").mkdir()
    (tmp_path / "utils" / "__init__.py").touch()
    (tmp_path / "utils" / "helpers.py").write_text("import models.base")
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "__init__.py").touch()
    (tmp_path / "models" / "base.py").write_text("# This is the base model")
    (tmp_path / "models" / "user.py").write_text("from .base import something")
    return tmp_path

def test_graph_builder(mock_project: Path):
    """Tests that the GraphBuilder correctly constructs the dependency graph."""
    builder = GraphBuilder(root_dir=mock_project)
    graph = builder.build_graph()

    assert "main.py" in graph
    assert "utils/helpers.py" in graph["main.py"]
    assert "models/user.py" in graph["main.py"]

    assert "utils/helpers.py" in graph
    assert "models/base.py" in graph["utils/helpers.py"]

    assert "models/user.py" in graph
    assert "models/base.py" in graph["models/user.py"]

    assert "models/base.py" in graph
    assert not graph["models/base.py"] # base.py imports nothing

def test_path_predictor(mock_project: Path):
    """Tests that the PathPredictor correctly identifies attack paths."""
    builder = GraphBuilder(root_dir=mock_project)
    graph = builder.build_graph()

    predictor = PathPredictor(graph)

    # If base.py is vulnerable, helpers.py and user.py depend on it.
    # And main.py depends on both of those.
    vulnerability_nodes = ["models/base.py"]
    predicted_paths = predictor.predict_paths(vulnerability_nodes)

    assert "models/base.py" in predicted_paths
    expected_path = sorted(["utils/helpers.py", "models/user.py", "main.py"])
    assert sorted(predicted_paths["models/base.py"]) == expected_path

    # If helpers.py is vulnerable, only main.py should be affected.
    vulnerability_nodes = ["utils/helpers.py"]
    predicted_paths = predictor.predict_paths(vulnerability_nodes)
    assert "utils/helpers.py" in predicted_paths
    assert predicted_paths["utils/helpers.py"] == ["main.py"]