"""
Tests for core/ modules: cache, config, lockfile, pins, trust, resolver.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from core.cache import CacheManager
from core.config import RaikuConfig
from core.lockfile import LockFile
from core.pins import PinManager
from core.trust import TrustManager
from core.resolver import DependencyResolver, DependencyError
from index.index_manager import IndexManager


# ===========================================================================
# CacheManager
# ===========================================================================

class TestCacheManager:

    def test_store_and_retrieve_file(self, cache_manager: CacheManager):
        cache_manager.store_file("Python", "pkg", "1.0.0", "raiku.toml", b"data")
        result = cache_manager.get_file("Python", "pkg", "1.0.0", "raiku.toml")
        assert result == b"data"

    def test_is_cached_false_without_meta(self, cache_manager: CacheManager):
        cache_manager.store_file("Python", "pkg", "1.0.0", "raiku.toml", b"data")
        assert not cache_manager.is_cached("Python", "pkg", "1.0.0")

    def test_is_cached_true_with_meta(self, cache_manager: CacheManager):
        cache_manager.store_file("Python", "pkg", "1.0.0", "raiku.toml", b"data")
        cache_manager.write_meta("Python", "pkg", "1.0.0", {"name": "pkg", "version": "1.0.0"})
        assert cache_manager.is_cached("Python", "pkg", "1.0.0")

    def test_evict_removes_directory(self, cache_manager: CacheManager):
        cache_manager.store_file("Python", "pkg", "1.0.0", "raiku.toml", b"data")
        cache_manager.write_meta("Python", "pkg", "1.0.0", {"name": "pkg"})
        assert cache_manager.evict("Python", "pkg", "1.0.0")
        assert not cache_manager.is_cached("Python", "pkg", "1.0.0")

    def test_evict_nonexistent_returns_false(self, cache_manager: CacheManager):
        assert not cache_manager.evict("Python", "ghost", "9.9.9")

    def test_hash_bytes_returns_64_hex(self, cache_manager: CacheManager):
        h = CacheManager.hash_bytes(b"hello raiku")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_total_size_bytes(self, cache_manager: CacheManager):
        cache_manager.store_file("Python", "pkg", "1.0.0", "raiku.toml", b"x" * 100)
        assert cache_manager.total_size_bytes() >= 100

    def test_list_cached_returns_meta(self, cache_manager: CacheManager):
        cache_manager.store_file("Python", "pkg", "1.0.0", "raiku.toml", b"d")
        cache_manager.write_meta("Python", "pkg", "1.0.0", {"name": "pkg", "version": "1.0.0"})
        items = cache_manager.list_cached()
        assert len(items) == 1
        assert items[0]["name"] == "pkg"


# ===========================================================================
# RaikuConfig
# ===========================================================================

class TestRaikuConfig:

    def test_defaults(self):
        cfg = RaikuConfig()
        assert cfg.safe_mode is True
        assert cfg.auto_trust is False
        assert cfg.readonly is False
        assert cfg.verbose is False
        assert cfg.color is True

    def test_readonly_field_persists(self, tmp_path: Path):
        import sys
        cfg = RaikuConfig()
        cfg.config_path = tmp_path / "config.toml"
        cfg.cache_dir = tmp_path / "cache"
        cfg.readonly = True
        # save() uses CONFIG_PATH constant; write the toml manually to cfg.config_path
        import tomli_w
        data = {
            "paths": {"cache_dir": str(cfg.cache_dir)},
            "remote": {"index_url": cfg.index_url, "raw_base_url": cfg.raw_base_url},
            "behaviour": {
                "safe_mode": cfg.safe_mode,
                "auto_trust": cfg.auto_trust,
                "verbose": cfg.verbose,
                "readonly": cfg.readonly,
            },
            "display": {"color": cfg.color},
        }
        with open(cfg.config_path, "wb") as fh:
            tomli_w.dump(data, fh)

        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        with open(cfg.config_path, "rb") as fh:
            loaded_data = tomllib.load(fh)
        loaded = RaikuConfig._from_dict(loaded_data)
        assert loaded.readonly is True

    def test_ensure_dirs_creates_cache(self, tmp_path: Path):
        cfg = RaikuConfig()
        cfg.cache_dir = tmp_path / "newcache"
        cfg.config_path = tmp_path / "config.toml"
        cfg.ensure_dirs()
        assert cfg.cache_dir.exists()


# ===========================================================================
# LockFile
# ===========================================================================

class TestLockFile:

    def test_add_and_is_locked(self, lock_file: LockFile):
        lock_file.add({"name": "fast-math", "version": "1.0.0",
                       "language": "Python", "path": "x", "sha256": "abc"})
        assert lock_file.is_locked("fast-math")

    def test_locked_version(self, lock_file: LockFile):
        lock_file.add({"name": "goqueue", "version": "2.3.1",
                       "language": "Go", "path": "y", "sha256": ""})
        assert lock_file.locked_version("goqueue") == "2.3.1"

    def test_remove_package(self, lock_file: LockFile):
        lock_file.add({"name": "pkg", "version": "1.0.0",
                       "language": "Python", "path": "", "sha256": ""})
        assert lock_file.remove("pkg")
        assert not lock_file.is_locked("pkg")

    def test_remove_nonexistent_returns_false(self, lock_file: LockFile):
        assert not lock_file.remove("ghost")

    def test_persists_to_disk(self, tmp_path: Path):
        lf = LockFile(tmp_path / "raiku.lock")
        lf.add({"name": "x", "version": "1.0.0", "language": "C", "path": "", "sha256": ""})
        lf.save()
        lf2 = LockFile(tmp_path / "raiku.lock")
        assert lf2.is_locked("x")

    def test_diff(self, lock_file: LockFile, tmp_path: Path):
        lock_file.add({"name": "a", "version": "1.0.0", "language": "Rust",
                       "path": "", "sha256": ""})
        other = LockFile(tmp_path / "other.lock")
        other.add({"name": "a", "version": "2.0.0", "language": "Rust",
                   "path": "", "sha256": ""})
        other.add({"name": "b", "version": "1.0.0", "language": "Go",
                   "path": "", "sha256": ""})
        diff = lock_file.diff(other)
        assert "a" in diff["changed"]
        assert "b" in diff["added"]


# ===========================================================================
# PinManager
# ===========================================================================

class TestPinManager:

    def test_pin_and_is_pinned(self, pin_manager: PinManager):
        pin_manager.pin("fast-math", "1.0.0")
        assert pin_manager.is_pinned("fast-math")

    def test_pinned_version(self, pin_manager: PinManager):
        pin_manager.pin("goqueue", "3.1.4", reason="stability")
        assert pin_manager.pinned_version("goqueue") == "3.1.4"

    def test_unpin(self, pin_manager: PinManager):
        pin_manager.pin("pkg", "1.0.0")
        assert pin_manager.unpin("pkg")
        assert not pin_manager.is_pinned("pkg")

    def test_unpin_nonexistent(self, pin_manager: PinManager):
        assert not pin_manager.unpin("ghost")

    def test_list_pins(self, pin_manager: PinManager):
        pin_manager.pin("a", "1.0.0")
        pin_manager.pin("b", "2.0.0")
        pins = pin_manager.list_pins()
        names = [p["name"] for p in pins]
        assert "a" in names
        assert "b" in names


# ===========================================================================
# TrustManager
# ===========================================================================

class TestTrustManager:

    def test_add_and_is_trusted(self, trust_manager: TrustManager):
        trust_manager.add("fast-math", reason="reviewed")
        assert trust_manager.is_trusted("fast-math")

    def test_not_trusted_by_default(self, trust_manager: TrustManager):
        assert not trust_manager.is_trusted("random-pkg")

    def test_remove_trust(self, trust_manager: TrustManager):
        trust_manager.add("pkg")
        assert trust_manager.remove("pkg")
        assert not trust_manager.is_trusted("pkg")

    def test_clear(self, trust_manager: TrustManager):
        trust_manager.add("a")
        trust_manager.add("b")
        count = trust_manager.clear()
        assert count == 2
        assert not trust_manager.is_trusted("a")

    def test_case_insensitive(self, trust_manager: TrustManager):
        trust_manager.add("FastMath")
        assert trust_manager.is_trusted("fastmath")


# ===========================================================================
# DependencyResolver
# ===========================================================================

def _make_manager(packages: list[dict]) -> IndexManager:
    manager = IndexManager()
    manager._data = {"schema_version": "1.0.0", "packages": packages}
    return manager


class TestDependencyResolver:

    def test_no_deps(self):
        manager = _make_manager([
            {"name": "a", "version": "1.0.0", "language": "Python",
             "path": "x", "dependencies": []},
        ])
        order = DependencyResolver(manager).resolve("a")
        assert order == ["a"]

    def test_single_dep(self):
        manager = _make_manager([
            {"name": "a", "version": "1.0.0", "language": "Python",
             "path": "x", "dependencies": ["b"]},
            {"name": "b", "version": "1.0.0", "language": "Python",
             "path": "y", "dependencies": []},
        ])
        order = DependencyResolver(manager).resolve("a")
        assert order.index("b") < order.index("a")

    def test_transitive_deps(self):
        manager = _make_manager([
            {"name": "a", "version": "1.0.0", "language": "Python",
             "path": "x", "dependencies": ["b"]},
            {"name": "b", "version": "1.0.0", "language": "Python",
             "path": "y", "dependencies": ["c"]},
            {"name": "c", "version": "1.0.0", "language": "Python",
             "path": "z", "dependencies": []},
        ])
        order = DependencyResolver(manager).resolve("a")
        assert order.index("c") < order.index("b") < order.index("a")

    def test_circular_dep_raises(self):
        manager = _make_manager([
            {"name": "x", "version": "1.0.0", "language": "Python",
             "path": "x", "dependencies": ["y"]},
            {"name": "y", "version": "1.0.0", "language": "Python",
             "path": "y", "dependencies": ["x"]},
        ])
        with pytest.raises(DependencyError, match="Circular"):
            DependencyResolver(manager).resolve("x")

    def test_missing_dep_raises(self):
        manager = _make_manager([
            {"name": "a", "version": "1.0.0", "language": "Python",
             "path": "x", "dependencies": ["missing"]},
        ])
        with pytest.raises(DependencyError, match="not found"):
            DependencyResolver(manager).resolve("a")

    def test_dependency_tree_string(self):
        manager = _make_manager([
            {"name": "a", "version": "1.0.0", "language": "Python",
             "path": "x", "dependencies": ["b"]},
            {"name": "b", "version": "1.0.0", "language": "Python",
             "path": "y", "dependencies": []},
        ])
        tree = DependencyResolver(manager).dependency_tree("a")
        assert "a" in tree
        assert "b" in tree
