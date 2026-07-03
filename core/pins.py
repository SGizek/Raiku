"""
Raiku pin manager.

Records packages that should never be auto-updated by raiku update --all.
Stored at ~/.raiku/pins.json.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from core.constants import RAIKU_HOME

PINS_PATH = RAIKU_HOME / "pins.json"


class PinManager:

    def __init__(self, pins_path: Path = PINS_PATH) -> None:
        self.pins_path = pins_path
        self._data: Optional[dict] = None

    def _load(self) -> dict:
        if self._data is not None:
            return self._data
        if self.pins_path.exists():
            try:
                self._data = json.loads(self.pins_path.read_text(encoding="utf-8"))
                return self._data
            except Exception:
                pass
        self._data = {"pins": {}}
        return self._data

    def _save(self) -> None:
        self.pins_path.parent.mkdir(parents=True, exist_ok=True)
        self.pins_path.write_text(
            json.dumps(self._load(), indent=2), encoding="utf-8"
        )

    def is_pinned(self, name: str) -> bool:
        return name.lower() in self._load().get("pins", {})

    def pin(self, name: str, version: str, reason: str = "") -> None:
        data = self._load()
        data.setdefault("pins", {})[name.lower()] = {
            "name":      name,
            "version":   version,
            "reason":    reason,
            "pinned_at": int(time.time()),
        }
        self._save()

    def unpin(self, name: str) -> bool:
        data = self._load()
        key = name.lower()
        if key in data.get("pins", {}):
            del data["pins"][key]
            self._save()
            return True
        return False

    def list_pins(self) -> list[dict]:
        return list(self._load().get("pins", {}).values())

    def pinned_version(self, name: str) -> Optional[str]:
        entry = self._load().get("pins", {}).get(name.lower())
        return entry["version"] if entry else None
