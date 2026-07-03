"""
Raiku cache manager.

Manages the ~/.raiku/cache/ directory tree.  Each installed package
lives under:

    ~/.raiku/cache/<language>/<package-name>/<version>/

The manager also maintains a lightweight metadata sidecar
(meta.json) alongside each cached package.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Optional

from core.constants import CACHE_DIR, HASH_ALGORITHM


class CacheManager:
    """High-level cache operations for the Raiku package store."""

    def __init__(self, cache_dir: Path = CACHE_DIR) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    def package_dir(self, language: str, name: str, version: str) -> Path:
        """Return the canonical cache path for a package version."""
        return self.cache_dir / language / name / version

    def is_cached(self, language: str, name: str, version: str) -> bool:
        """Return True if the package version is already in cache."""
        pkg_dir = self.package_dir(language, name, version)
        meta = pkg_dir / "meta.json"
        return pkg_dir.exists() and meta.exists()

    # ------------------------------------------------------------------
    # Store / retrieve
    # ------------------------------------------------------------------
    def store_file(
        self,
        language: str,
        name: str,
        version: str,
        filename: str,
        content: bytes,
    ) -> Path:
        """Write raw bytes to the cache and return the file path."""
        dest_dir = self.package_dir(language, name, version)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        dest.write_bytes(content)
        return dest

    def write_meta(
        self,
        language: str,
        name: str,
        version: str,
        meta: dict,
    ) -> None:
        """Persist package metadata sidecar."""
        dest_dir = self.package_dir(language, name, version)
        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / "meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

    def read_meta(
        self,
        language: str,
        name: str,
        version: str,
    ) -> Optional[dict]:
        """Load package metadata sidecar, or None if not cached."""
        meta_path = self.package_dir(language, name, version) / "meta.json"
        if not meta_path.exists():
            return None
        return json.loads(meta_path.read_text(encoding="utf-8"))

    def get_file(
        self,
        language: str,
        name: str,
        version: str,
        filename: str,
    ) -> Optional[bytes]:
        """Return cached file bytes, or None if not present."""
        path = self.package_dir(language, name, version) / filename
        if not path.exists():
            return None
        return path.read_bytes()

    # ------------------------------------------------------------------
    # Hash helpers
    # ------------------------------------------------------------------
    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """Return hex digest of data using the configured algorithm."""
        h = hashlib.new(HASH_ALGORITHM)
        h.update(data)
        return h.hexdigest()

    @staticmethod
    def hash_file(path: Path) -> str:
        """Return hex digest of a file on disk."""
        h = hashlib.new(HASH_ALGORITHM)
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    # ------------------------------------------------------------------
    # Eviction
    # ------------------------------------------------------------------
    def evict(self, language: str, name: str, version: str) -> bool:
        """Remove a specific package version from cache. Returns True on success."""
        pkg_dir = self.package_dir(language, name, version)
        if pkg_dir.exists():
            shutil.rmtree(pkg_dir)
            return True
        return False

    def list_cached(self) -> list[dict]:
        """Return a list of all cached packages with their metadata."""
        packages = []
        for lang_dir in sorted(self.cache_dir.iterdir()):
            if not lang_dir.is_dir():
                continue
            for pkg_dir in sorted(lang_dir.iterdir()):
                if not pkg_dir.is_dir():
                    continue
                for ver_dir in sorted(pkg_dir.iterdir()):
                    if not ver_dir.is_dir():
                        continue
                    meta_path = ver_dir / "meta.json"
                    if meta_path.exists():
                        try:
                            meta = json.loads(meta_path.read_text(encoding="utf-8"))
                            packages.append(meta)
                        except json.JSONDecodeError:
                            pass
        return packages

    def total_size_bytes(self) -> int:
        """Return total disk usage of the cache in bytes."""
        total = 0
        for path in self.cache_dir.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
        return total
