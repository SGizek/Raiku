"""Tests for index/ module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from index.index_manager import IndexManager, IndexError


class TestIndexManager:

    def test_load_valid_index(self, index_file: Path):
        manager = IndexManager(index_path=index_file)
        data = manager.load()
        assert "packages" in data
        assert len(data["packages"]) == 3

    def test_load_missing_raises(self, tmp_path: Path):
        manager = IndexManager(index_path=tmp_path / "nope.json")
        with pytest.raises(IndexError, match="No local index"):
            manager.load()

    def test_find_existing_package(self, index_file: Path):
        manager = IndexManager(index_path=index_file)
        pkg = manager.find("fast-math")
        assert pkg is not None
        assert pkg["language"] == "Python"

    def test_find_case_insensitive(self, index_file: Path):
        manager = IndexManager(index_path=index_file)
        assert manager.find("FAST-MATH") is not None

    def test_find_nonexistent_returns_none(self, index_file: Path):
        manager = IndexManager(index_path=index_file)
        assert manager.find("does-not-exist") is None

    def test_search_by_name(self, index_file: Path):
        manager = IndexManager(index_path=index_file)
        results = manager.search("math")
        assert any(p["name"] == "fast-math" for p in results)

    def test_search_by_language(self, index_file: Path):
        manager = IndexManager(index_path=index_file)
        results = manager.search("", language="Go")
        assert all(p["language"] == "Go" for p in results)

    def test_search_no_results(self, index_file: Path):
        manager = IndexManager(index_path=index_file)
        assert manager.search("xyznonexistent123") == []

    def test_list_all(self, index_file: Path):
        manager = IndexManager(index_path=index_file)
        all_pkgs = manager.list_all()
        assert len(all_pkgs) == 3

    def test_list_all_filtered_by_language(self, index_file: Path):
        manager = IndexManager(index_path=index_file)
        go_pkgs = manager.list_all(language="Go")
        assert all(p["language"] == "Go" for p in go_pkgs)

    def test_stats(self, index_file: Path):
        manager = IndexManager(index_path=index_file)
        stats = manager.stats()
        assert stats["total"] == 3
        assert "Go" in stats["by_language"]
        assert stats["by_language"]["Go"] == 1

    def test_is_stale_without_synced_at(self, tmp_path: Path):
        data = {"schema_version": "1.0.0", "packages": []}
        p = tmp_path / "index.json"
        p.write_text(json.dumps(data))
        manager = IndexManager(index_path=p)
        assert manager.is_stale()

    def test_not_stale_with_recent_synced_at(self, tmp_path: Path):
        import time
        data = {"schema_version": "1.0.0", "packages": [], "_synced_at": int(time.time())}
        p = tmp_path / "index.json"
        p.write_text(json.dumps(data))
        manager = IndexManager(index_path=p)
        assert not manager.is_stale()

    def test_corrupt_json_raises(self, tmp_path: Path):
        p = tmp_path / "index.json"
        p.write_text("{ not valid json }")
        manager = IndexManager(index_path=p)
        with pytest.raises(IndexError):
            manager.load()
