from __future__ import annotations
import ast
from pathlib import Path
from typing import Dict, List, Set

class GraphBuilder:
    """
    Builds a directed graph representing the codebase structure.
    """

    def __init__(self, root_dir: str | Path = "."):
        self.root_dir = Path(root_dir).resolve()
        self.graph: Dict[str, Set[str]] = {}

    def build_graph(self) -> Dict[str, List[str]]:
        """
        Scans the repository to build a file-based import graph.
        Nodes are file paths, and an edge from A to B exists if A imports B.
        """
        py_files = list(self.root_dir.rglob("*.py"))

        for file_path in py_files:
            relative_path = str(file_path.relative_to(self.root_dir))
            self.graph[relative_path] = set()

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(file_path))

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                self._resolve_import(alias.name, relative_path, py_files, level=0)
                        elif isinstance(node, ast.ImportFrom):
                            # For ImportFrom, module can be None (e.g., from . import foo)
                            if node.module:
                                self._resolve_import(node.module, relative_path, py_files, level=node.level)
            except Exception:
                # Ignore files that can't be parsed
                continue

        # Convert sets to lists for the final output
        return {k: sorted(list(v)) for k, v in self.graph.items()}

    def _resolve_import(self, module_name: str, current_file: str, all_files: List[Path], level: int = 0):
        """
        Resolves an import name to a file path within the repository.
        """
        possible_paths = []
        if level > 0:
            # Relative import
            base_dir = Path(current_file).parent
            for _ in range(level - 1):
                base_dir = base_dir.parent

            module_path_parts = module_name.split('.')
            possible_path = base_dir.joinpath(*module_path_parts)

            possible_paths.append(possible_path.with_suffix(".py"))
            possible_paths.append(possible_path / "__init__.py")
        else:
            # Absolute import
            module_path_parts = module_name.split('.')
            possible_paths.append(Path(*module_path_parts).with_suffix(".py"))
            possible_paths.append(Path(*module_path_parts) / "__init__.py")

        for p in all_files:
            relative_p = p.relative_to(self.root_dir)
            if relative_p in possible_paths:
                self.graph[current_file].add(str(relative_p))
                return