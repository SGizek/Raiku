"""
Raiku trust manager.

Manages the per-machine trusted package list stored at ~/.raiku/trusted.json.

A trusted package bypasses the interactive build-command confirmation prompt
when installed with `raiku install`. Trust is always an explicit user action —
it is never granted automatically.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from core.constants import TRUST_DB_PATH


class TrustManager:
    """Persist and query the local trusted-packages database."""

    def __init__(self, db_path: Path = TRUST_DB_PATH) -> None:
        self.db_path = db_path
        self._data: Optional[dict] = None

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        if self._data is not None:
            return self._data
        if self.db_path.exists():
            try:
                self._data = json.loads(self.db_path.read_text(encoding="utf-8"))
                return self._data
            except (json.JSONDecodeError, OSError):
                pass
        self._data = {"trusted": {}}
        return self._data

    def _save(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.write_text(
            json.dumps(self._load(), indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_trusted(self, name: str) -> bool:
        """Return True if *name* is in the trusted list."""
        return name.lower() in self._load().get("trusted", {})

    def add(self, name: str, reason: str = "") -> None:
        """Mark *name* as trusted."""
        data = self._load()
        data.setdefault("trusted", {})[name.lower()] = {
            "name": name,
            "trusted_at": int(time.time()),
            "reason": reason,
        }
        self._save()

    def remove(self, name: str) -> bool:
        """Remove *name* from the trusted list. Returns True if it was present."""
        data = self._load()
        key = name.lower()
        if key in data.get("trusted", {}):
            del data["trusted"][key]
            self._save()
            return True
        return False

    def list_trusted(self) -> list[dict]:
        """Return all trusted package records."""
        return list(self._load().get("trusted", {}).values())

    def clear(self) -> int:
        """Remove all trusted packages. Returns count removed."""
        data = self._load()
        count = len(data.get("trusted", {}))
        data["trusted"] = {}
        self._save()
        return count
