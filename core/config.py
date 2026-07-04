"""
Raiku configuration manager.

Reads and writes ~/.raiku/config.toml. Provides typed access to
all user-configurable settings with safe defaults.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from core.constants import CONFIG_PATH, CACHE_DIR, INDEX_URL, RAW_BASE_URL


@dataclass
class RaikuConfig:
    """Typed representation of ~/.raiku/config.toml."""

    # Paths
    cache_dir: Path = field(default_factory=lambda: CACHE_DIR)
    config_path: Path = field(default_factory=lambda: CONFIG_PATH)

    # Remote
    index_url: str = INDEX_URL
    raw_base_url: str = RAW_BASE_URL

    # Behaviour
    safe_mode: bool = True          # Always prompt before running build commands
    auto_trust: bool = False        # Never silently mark packages as trusted
    verbose: bool = False
    readonly: bool = False          # Prevent all cache writes when True

    # Display
    color: bool = True

    # Internal — not written to disk
    _loaded: bool = field(default=False, init=False, repr=False, compare=False)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
    @classmethod
    def load(cls) -> "RaikuConfig":
        """Load config from disk, falling back to defaults if missing."""
        cfg = cls()
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "rb") as fh:
                    data = tomllib.load(fh)
                cfg = cls._from_dict(data)
            except Exception:
                # Corrupt config — use defaults, don't crash
                pass
        cfg._loaded = True
        return cfg

    @classmethod
    def _from_dict(cls, data: dict) -> "RaikuConfig":
        paths = data.get("paths", {})
        remote = data.get("remote", {})
        behaviour = data.get("behaviour", {})
        display = data.get("display", {})

        return cls(
            cache_dir=Path(paths.get("cache_dir", CACHE_DIR)),
            index_url=remote.get("index_url", INDEX_URL),
            raw_base_url=remote.get("raw_base_url", RAW_BASE_URL),
            safe_mode=behaviour.get("safe_mode", True),
            auto_trust=behaviour.get("auto_trust", False),
            verbose=behaviour.get("verbose", False),
            readonly=behaviour.get("readonly", False),
            color=display.get("color", True),
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self) -> None:
        """Write current config to disk."""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "paths": {"cache_dir": str(self.cache_dir)},
            "remote": {
                "index_url": self.index_url,
                "raw_base_url": self.raw_base_url,
            },
            "behaviour": {
                "safe_mode": self.safe_mode,
                "auto_trust": self.auto_trust,
                "verbose": self.verbose,
                "readonly": self.readonly,
            },
            "display": {"color": self.color},
        }
        with open(CONFIG_PATH, "wb") as fh:
            tomli_w.dump(data, fh)

    def ensure_dirs(self) -> None:
        """Create all required Raiku home directories."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
