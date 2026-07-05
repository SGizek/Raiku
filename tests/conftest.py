"""
Shared pytest fixtures for the Raiku test suite.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner

from cli.main import main as raiku_cli
from core.cache import CacheManager
from core.config import RaikuConfig
from core.lockfile import LockFile
from core.pins import PinManager
from core.trust import TrustManager
from installer.cache_store import CacheStore


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

@pytest.fixture
def runner() -> CliRunner:
    """Click test runner with mix_stderr=False for clean output separation."""
    return CliRunner(mix_stderr=False)


@pytest.fixture
def invoke(runner: CliRunner):
    """Helper that invokes the Raiku CLI and returns the result."""
    def _invoke(*args: str, input: str | None = None):
        return runner.invoke(raiku_cli, list(args), input=input, catch_exceptions=False)
    return _invoke


# ---------------------------------------------------------------------------
# Temporary directories and config
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Return a clean temporary directory."""
    return tmp_path


@pytest.fixture
def tmp_cache(tmp_path: Path) -> Path:
    """Return a temp directory to use as the Raiku cache."""
    cache = tmp_path / "cache"
    cache.mkdir()
    return cache


@pytest.fixture
def cache_manager(tmp_cache: Path) -> CacheManager:
    return CacheManager(tmp_cache)


@pytest.fixture
def cache_store(tmp_cache: Path) -> CacheStore:
    return CacheStore(tmp_cache)


@pytest.fixture
def raiku_config(tmp_path: Path) -> RaikuConfig:
    """Return a RaikuConfig pointing at a temp cache so tests don't touch ~/.raiku."""
    cfg = RaikuConfig()
    cfg.cache_dir = tmp_path / "cache"
    cfg.cache_dir.mkdir()
    cfg.safe_mode = False   # Don't prompt in tests
    cfg.color = False
    return cfg


# ---------------------------------------------------------------------------
# Sample package manifests
# ---------------------------------------------------------------------------

SAMPLE_MANIFEST = {
    "name": "test-pkg",
    "version": "1.0.0",
    "language": "Python",
    "author": "Test Author",
    "description": "A test package.",
    "license": "MIT",
    "build_command": "pip install -e .",
    "dependencies": [],
}

SAMPLE_VERSION_DATA = {
    "version": "1.0.0",
    "release_date": "2026-07-04",
    "stability_level": "stable",
    "changelog": ["Initial release"],
}


@pytest.fixture
def sample_package_dir(tmp_path: Path) -> Path:
    """Create a minimal valid Raiku package directory."""
    pkg_dir = tmp_path / "test-pkg"
    pkg_dir.mkdir()
    src_dir = pkg_dir / "src"
    src_dir.mkdir()

    import tomli_w, yaml

    with open(pkg_dir / "raiku.toml", "wb") as f:
        tomli_w.dump(SAMPLE_MANIFEST, f)

    with open(pkg_dir / "version.yml", "w", encoding="utf-8") as f:
        yaml.dump(SAMPLE_VERSION_DATA, f, default_flow_style=False)

    (pkg_dir / "README.md").write_text("# test-pkg\nA test package.", encoding="utf-8")
    (src_dir / "test_pkg.py").write_text('def hello(): return "hello"', encoding="utf-8")

    return pkg_dir


@pytest.fixture
def sample_index() -> dict:
    """Minimal valid index with 3 packages covering different languages."""
    return {
        "schema_version": "1.0.0",
        "generated_by": "test",
        "_synced_at": 9999999999,
        "packages": [
            {
                "name": "fast-math",
                "version": "1.0.0",
                "language": "Python",
                "author": "Ada Lovelace",
                "description": "High-performance math utilities.",
                "path": "UserSub/Python/fast-math",
                "tags": ["math", "vectors"],
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            {
                "name": "goqueue",
                "version": "1.0.0",
                "language": "Go",
                "author": "Rob Pike",
                "description": "Thread-safe generic queue for Go.",
                "path": "UserSub/Go/goqueue",
                "tags": ["queue", "concurrency"],
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            {
                "name": "zigutils",
                "version": "2.0.0",
                "language": "Zig",
                "author": "Andrew Kelley",
                "description": "Utility functions for Zig.",
                "path": "UserSub/Zig/zigutils",
                "tags": ["utils"],
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
        ],
    }


@pytest.fixture
def index_file(tmp_path: Path, sample_index: dict) -> Path:
    """Write sample_index to a temp file and return its path."""
    p = tmp_path / "index.json"
    p.write_text(json.dumps(sample_index), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Trust / pin / lock helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def trust_manager(tmp_path: Path) -> TrustManager:
    return TrustManager(db_path=tmp_path / "trusted.json")


@pytest.fixture
def pin_manager(tmp_path: Path) -> PinManager:
    return PinManager(pins_path=tmp_path / "pins.json")


@pytest.fixture
def lock_file(tmp_path: Path) -> LockFile:
    return LockFile(tmp_path / "raiku.lock")
