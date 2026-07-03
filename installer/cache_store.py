"""
Raiku cache store.

Writes fetched package files to ~/.raiku/cache/ and provides
metadata persistence for installed packages.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from core.cache import CacheManager
from core.constants import CACHE_DIR


class CacheStore:
    """Persists downloaded package files and metadata to the local cache."""

    def __init__(self, cache_dir: Path = CACHE_DIR) -> None:
        self.manager = CacheManager(cache_dir)

    def store_package(
        self,
        language: str,
        name: str,
        version: str,
        files: dict[str, bytes],
        index_entry: dict[str, Any],
        hashes: Optional[dict[str, str]] = None,
    ) -> Path:
        """
        Write all fetched *files* (filename → bytes) to the cache.
        Records metadata sidecar.
        Returns the package cache directory path.
        """
        pkg_dir = self.manager.package_dir(language, name, version)

        for filename, content in files.items():
            self.manager.store_file(language, name, version, filename, content)

        meta = {
            "name": name,
            "version": version,
            "language": language,
            "path": index_entry.get("path", ""),
            "author": index_entry.get("author", ""),
            "description": index_entry.get("description", ""),
            "installed_at": int(time.time()),
            "hashes": hashes or {},
            "sha256_index": index_entry.get("sha256", ""),
        }
        self.manager.write_meta(language, name, version, meta)

        return pkg_dir

    def is_cached(self, language: str, name: str, version: str) -> bool:
        return self.manager.is_cached(language, name, version)

    def get_package_dir(self, language: str, name: str, version: str) -> Optional[Path]:
        pkg_dir = self.manager.package_dir(language, name, version)
        return pkg_dir if pkg_dir.exists() else None

    def read_meta(self, language: str, name: str, version: str) -> Optional[dict]:
        return self.manager.read_meta(language, name, version)

    def list_installed(self) -> list[dict]:
        return self.manager.list_cached()

    def evict(self, language: str, name: str, version: str) -> bool:
        return self.manager.evict(language, name, version)
