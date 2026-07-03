"""
Raiku lock file manager.

Writes and reads raiku.lock — a JSON file that records the exact versions
of every installed package so installs are reproducible across machines.

Format:
{
  "lock_version": "1",
  "generated_at": <unix timestamp>,
  "packages": {
    "<name>": {
      "version": "1.0.0",
      "language": "Python",
      "path": "UserSub/Python/fast-math",
      "sha256": "<hex>",
      "installed_at": <unix timestamp>
    },
    ...
  }
}
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional


LOCK_FILENAME = "raiku.lock"


class LockFile:
    """Read/write the raiku.lock file in the current working directory."""

    LOCK_VERSION = "1"

    def __init__(self, lock_path: Path) -> None:
        self.lock_path = lock_path
        self._data: Optional[dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def load(self) -> dict[str, Any]:
        if self._data is not None:
            return self._data
        if self.lock_path.exists():
            try:
                self._data = json.loads(self.lock_path.read_text(encoding="utf-8"))
                return self._data
            except (json.JSONDecodeError, OSError):
                pass
        self._data = {
            "lock_version": self.LOCK_VERSION,
            "generated_at": int(time.time()),
            "packages": {},
        }
        return self._data

    def save(self) -> None:
        data = self.load()
        data["generated_at"] = int(time.time())
        self.lock_path.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------------
    # Package operations
    # ------------------------------------------------------------------

    def add(self, entry: dict[str, Any]) -> None:
        """Record an installed package in the lock file."""
        data = self.load()
        name = entry["name"]
        data["packages"][name] = {
            "version":      entry.get("version", ""),
            "language":     entry.get("language", ""),
            "path":         entry.get("path", ""),
            "sha256":       entry.get("sha256", ""),
            "installed_at": int(time.time()),
        }
        self.save()

    def remove(self, name: str) -> bool:
        data = self.load()
        if name in data["packages"]:
            del data["packages"][name]
            self.save()
            return True
        return False

    def get(self, name: str) -> Optional[dict[str, Any]]:
        return self.load()["packages"].get(name)

    def all_packages(self) -> dict[str, Any]:
        return dict(self.load()["packages"])

    def is_locked(self, name: str) -> bool:
        return name in self.load()["packages"]

    def locked_version(self, name: str) -> Optional[str]:
        pkg = self.get(name)
        return pkg["version"] if pkg else None

    def diff(self, other_lock: "LockFile") -> dict[str, Any]:
        """
        Compare this lock file against another.
        Returns dict with keys: added, removed, changed.
        """
        mine  = self.all_packages()
        other = other_lock.all_packages()

        added   = {k: v for k, v in other.items() if k not in mine}
        removed = {k: v for k, v in mine.items()  if k not in other}
        changed = {
            k: {"from": mine[k]["version"], "to": other[k]["version"]}
            for k in mine
            if k in other and mine[k]["version"] != other[k]["version"]
        }
        return {"added": added, "removed": removed, "changed": changed}
