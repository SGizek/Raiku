"""
Raiku YAML parser.

Reads and writes version.yml package version manifests.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from core.constants import VERSION_YML, STABILITY_LEVELS


class YamlParseError(Exception):
    """Raised when a version.yml cannot be parsed or is structurally invalid."""


_REQUIRED_KEYS: tuple[str, ...] = (
    "version",
    "release_date",
    "changelog",
    "stability_level",
)


def parse_version_yml(path: Path) -> dict[str, Any]:
    """
    Parse a version.yml file and return its contents as a dict.

    Raises YamlParseError on any structural problem.
    """
    yml_path = path if path.name == VERSION_YML else path / VERSION_YML

    if not yml_path.exists():
        raise YamlParseError(f"version.yml not found at: {yml_path}")

    try:
        with open(yml_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise YamlParseError(f"Failed to parse YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise YamlParseError(f"{yml_path}: top-level must be a YAML mapping")

    _validate_required_keys(data, yml_path)
    _validate_version_string(data, yml_path)
    _validate_stability(data, yml_path)
    _validate_changelog(data, yml_path)
    _validate_release_date(data, yml_path)

    return data


def write_version_yml(path: Path, data: dict[str, Any]) -> None:
    """
    Write a version.yml to *path* (directory or full file path).
    """
    _validate_required_keys(data, path)

    yml_path = path if path.name == VERSION_YML else path / VERSION_YML
    yml_path.parent.mkdir(parents=True, exist_ok=True)

    with open(yml_path, "w", encoding="utf-8") as fh:
        yaml.dump(data, fh, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ---------------------------------------------------------------------------
# Internal validators
# ---------------------------------------------------------------------------

def _validate_required_keys(data: dict, path: Path) -> None:
    missing = [k for k in _REQUIRED_KEYS if k not in data]
    if missing:
        raise YamlParseError(
            f"{path}: missing required key(s): {', '.join(missing)}"
        )


def _validate_version_string(data: dict, path: Path) -> None:
    version = data.get("version", "")
    if not version or not isinstance(version, str):
        raise YamlParseError(f"{path}: 'version' must be a non-empty string")
    if not re.fullmatch(r"\d+\.\d+\.\d+.*", str(version)):
        raise YamlParseError(
            f"{path}: 'version' must follow semver (e.g. 1.0.0)"
        )


def _validate_stability(data: dict, path: Path) -> None:
    level = data.get("stability_level", "")
    if level not in STABILITY_LEVELS:
        raise YamlParseError(
            f"{path}: 'stability_level' must be one of: "
            f"{', '.join(STABILITY_LEVELS)}. Got: '{level}'"
        )


def _validate_changelog(data: dict, path: Path) -> None:
    changelog = data.get("changelog")
    if not changelog or not isinstance(changelog, (str, list)):
        raise YamlParseError(
            f"{path}: 'changelog' must be a non-empty string or list of strings"
        )


def _validate_release_date(data: dict, path: Path) -> None:
    date = data.get("release_date", "")
    # Accept YYYY-MM-DD format (yaml may parse as date object already)
    if hasattr(date, "isoformat"):
        return  # datetime.date object — valid
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(date)):
        raise YamlParseError(
            f"{path}: 'release_date' must be YYYY-MM-DD format"
        )
