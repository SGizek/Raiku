"""
Raiku dependency resolver.

Resolves the full installation order for a package and its transitive
dependencies using a depth-first topological sort. Detects circular
dependencies and reports them clearly.
"""
from __future__ import annotations

from typing import Optional

from index.index_manager import IndexManager


class DependencyError(Exception):
    """Raised when dependency resolution fails."""


class DependencyResolver:
    """
    Resolves transitive dependencies for a package.

    Uses the index as the source of truth for dependency metadata.
    """

    def __init__(self, manager: IndexManager) -> None:
        self.manager = manager

    def resolve(self, root_name: str) -> list[str]:
        """
        Return an ordered list of package names that must be installed
        before *root_name* (dependencies first, root last).

        Raises DependencyError on circular dependencies or missing packages.
        """
        order: list[str] = []
        visited: set[str] = set()
        in_stack: set[str] = set()

        self._visit(root_name, order, visited, in_stack, path=[root_name])
        return order

    def resolve_many(self, names: list[str]) -> list[str]:
        """Resolve multiple root packages, deduplicating the result."""
        seen: set[str] = set()
        result: list[str] = []
        for name in names:
            for pkg in self.resolve(name):
                if pkg not in seen:
                    seen.add(pkg)
                    result.append(pkg)
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _visit(
        self,
        name: str,
        order: list[str],
        visited: set[str],
        in_stack: set[str],
        path: list[str],
    ) -> None:
        if name in visited:
            return

        if name in in_stack:
            cycle = " → ".join(path)
            raise DependencyError(
                f"Circular dependency detected: {cycle}"
            )

        entry = self.manager.find(name)
        if entry is None:
            raise DependencyError(
                f"Dependency '{name}' not found in index. "
                "Run 'raiku sync' to refresh the index."
            )

        in_stack.add(name)
        deps: list[str] = entry.get("dependencies", [])

        for dep in deps:
            self._visit(dep, order, visited, in_stack, path + [dep])

        in_stack.discard(name)
        visited.add(name)
        order.append(name)

    def dependency_tree(self, name: str, indent: int = 0) -> str:
        """Return a human-readable dependency tree string."""
        entry = self.manager.find(name)
        if entry is None:
            return "  " * indent + f"[?] {name} (not in index)"

        lines = ["  " * indent + f"{'└─ ' if indent else ''}{name} v{entry.get('version', '?')}"]
        for dep in entry.get("dependencies", []):
            lines.append(self.dependency_tree(dep, indent + 1))
        return "\n".join(lines)
