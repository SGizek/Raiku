"""
Raiku index manager.

Manages the local index cache at ~/.raiku/index.json and provides
search / lookup operations. The index is the single source of truth
for all package resolution — no folder scanning is ever performed.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

import requests

from core.constants import INDEX_CACHE_PATH, INDEX_URL, SUPPORTED_LANGUAGES


class IndexError(Exception):
    """Raised on index fetch or parse failures."""


class IndexManager:
    """Load, sync, search, and resolve packages via index.json."""

    # Maximum age of a local index before sync is recommended (seconds)
    STALE_THRESHOLD: int = 3600  # 1 hour

    def __init__(
        self,
        index_path: Path = INDEX_CACHE_PATH,
        index_url: str = INDEX_URL,
    ) -> None:
        self.index_path = index_path
        self.index_url = index_url
        self._data: Optional[dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Load / sync
    # ------------------------------------------------------------------

    def load(self) -> dict[str, Any]:
        """
        Return the index data, loading from disk if needed.
        Raises IndexError if no local copy exists and fetch fails.
        """
        if self._data is not None:
            return self._data

        if self.index_path.exists():
            try:
                self._data = json.loads(
                    self.index_path.read_text(encoding="utf-8")
                )
                return self._data
            except json.JSONDecodeError as exc:
                raise IndexError(
                    f"Local index is corrupt: {exc}. Run 'raiku sync' to refresh."
                ) from exc

        raise IndexError(
            "No local index found. Run 'raiku sync' to download it."
        )

    def sync(self, timeout: int = 30) -> dict[str, Any]:
        """
        Fetch the latest index from the remote repository and cache it locally.
        Returns the fresh index data.
        """
        try:
            resp = requests.get(self.index_url, timeout=timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise IndexError(f"Failed to fetch index: {exc}") from exc

        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise IndexError(f"Remote index is not valid JSON: {exc}") from exc

        _validate_index_structure(data)

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        # Stamp sync time
        data["_synced_at"] = int(time.time())
        self.index_path.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )
        self._data = data
        return data

    def is_stale(self) -> bool:
        """Return True if the local index is older than STALE_THRESHOLD."""
        if not self.index_path.exists():
            return True
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        synced_at = data.get("_synced_at", 0)
        return (time.time() - synced_at) > self.STALE_THRESHOLD

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------

    def find(self, name: str) -> Optional[dict[str, Any]]:
        """
        Find a package by exact name. Returns the index entry or None.
        Case-insensitive.
        """
        data = self.load()
        packages = data.get("packages", [])
        name_lower = name.lower()
        for pkg in packages:
            if pkg.get("name", "").lower() == name_lower:
                return pkg
        return None

    def search(self, query: str, language: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Search packages by name, description, or author substring.
        Optionally filter by language.
        Returns a list of matching index entries.
        """
        data = self.load()
        packages = data.get("packages", [])
        query_lower = query.lower()
        results = []

        for pkg in packages:
            # Language filter
            if language:
                if pkg.get("language", "").lower() != language.lower():
                    continue

            # Substring match across searchable fields
            haystack = " ".join([
                pkg.get("name", ""),
                pkg.get("description", ""),
                pkg.get("author", ""),
                pkg.get("language", ""),
            ]).lower()

            if query_lower in haystack:
                results.append(pkg)

        return results

    def list_all(self, language: Optional[str] = None) -> list[dict[str, Any]]:
        """Return all packages, optionally filtered by language."""
        data = self.load()
        packages = data.get("packages", [])
        if language:
            return [p for p in packages if p.get("language", "").lower() == language.lower()]
        return packages

    def stats(self) -> dict[str, Any]:
        """Return aggregate stats about the index."""
        data = self.load()
        packages = data.get("packages", [])
        by_language: dict[str, int] = {}
        for pkg in packages:
            lang = pkg.get("language", "unknown")
            by_language[lang] = by_language.get(lang, 0) + 1
        return {
            "total": len(packages),
            "by_language": by_language,
            "schema_version": data.get("schema_version", "unknown"),
            "synced_at": data.get("_synced_at"),
        }


# ---------------------------------------------------------------------------
# Index structure validator
# ---------------------------------------------------------------------------

def _validate_index_structure(data: dict) -> None:
    if not isinstance(data, dict):
        raise IndexError("index.json must be a JSON object at the top level")
    if "packages" not in data:
        raise IndexError("index.json missing required 'packages' array")
    if not isinstance(data["packages"], list):
        raise IndexError("index.json 'packages' must be an array")

    required_pkg_fields = ("name", "version", "language", "path")
    for i, pkg in enumerate(data["packages"]):
        missing = [f for f in required_pkg_fields if f not in pkg]
        if missing:
            raise IndexError(
                f"Package at index {i} missing field(s): {', '.join(missing)}"
            )
        if pkg.get("language") not in SUPPORTED_LANGUAGES:
            raise IndexError(
                f"Package '{pkg.get('name')}' has unsupported language: "
                f"'{pkg.get('language')}'"
            )
