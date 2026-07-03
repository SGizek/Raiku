"""
Raiku TOML parser.

Reads and writes raiku.toml package manifests with full field validation
at the parse layer (structural validation; schema enforcement is in
validator/).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from core.constants import RAIKU_TOML, SUPPORTED_LANGUAGES


class TomlParseError(Exception):
    """Raised when a raiku.toml cannot be parsed or is structurally invalid."""


# ---------------------------------------------------------------------------
# Required and optional top-level keys
# ---------------------------------------------------------------------------
_REQUIRED_KEYS: tuple[str, ...] = (
    "name",
    "version",
    "language",
    "author",
    "build_command",
)

_OPTIONAL_KEYS: tuple[str, ...] = ("dependencies", "description", "license", "homepage")


def parse_raiku_toml(path: Path) -> dict[str, Any]:
    """
    Parse a raiku.toml file and return its contents as a dict.

    Raises TomlParseError on any structural problem.
    """
    toml_path = path if path.name == RAIKU_TOML else path / RAIKU_TOML

    if not toml_path.exists():
        raise TomlParseError(f"raiku.toml not found at: {toml_path}")

    try:
        with open(toml_path, "rb") as fh:
            data = tomllib.load(fh)
    except Exception as exc:
        raise TomlParseError(f"Failed to parse TOML: {exc}") from exc

    _validate_required_keys(data, toml_path)
    _validate_language(data, toml_path)
    _validate_name(data, toml_path)
    _validate_version_string(data, toml_path)
    _validate_dependencies(data, toml_path)

    return data


def write_raiku_toml(path: Path, data: dict[str, Any]) -> None:
    """
    Write a raiku.toml to *path* (directory or full file path).

    Raises TomlParseError if data is structurally invalid before writing.
    """
    _validate_required_keys(data, path)

    toml_path = path if path.name == RAIKU_TOML else path / RAIKU_TOML
    toml_path.parent.mkdir(parents=True, exist_ok=True)

    with open(toml_path, "wb") as fh:
        tomli_w.dump(data, fh)


# ---------------------------------------------------------------------------
# Internal validators
# ---------------------------------------------------------------------------

def _validate_required_keys(data: dict, path: Path) -> None:
    missing = [k for k in _REQUIRED_KEYS if k not in data]
    if missing:
        raise TomlParseError(
            f"{path}: missing required key(s): {', '.join(missing)}"
        )


def _validate_language(data: dict, path: Path) -> None:
    lang = data.get("language", "")
    if lang not in SUPPORTED_LANGUAGES:
        raise TomlParseError(
            f"{path}: unsupported language '{lang}'. "
            f"Supported: {', '.join(SUPPORTED_LANGUAGES)}"
        )


def _validate_name(data: dict, path: Path) -> None:
    name = data.get("name", "")
    if not name or not isinstance(name, str):
        raise TomlParseError(f"{path}: 'name' must be a non-empty string")
    # Allow letters, digits, hyphens, underscores only
    import re
    if not re.fullmatch(r"[a-zA-Z0-9_\-]+", name):
        raise TomlParseError(
            f"{path}: 'name' contains invalid characters. "
            "Only letters, digits, hyphens, and underscores are allowed."
        )


def _validate_version_string(data: dict, path: Path) -> None:
    version = data.get("version", "")
    if not version or not isinstance(version, str):
        raise TomlParseError(f"{path}: 'version' must be a non-empty string")
    import re
    if not re.fullmatch(r"\d+\.\d+\.\d+.*", version):
        raise TomlParseError(
            f"{path}: 'version' must follow semver (e.g. 1.0.0)"
        )


def _validate_dependencies(data: dict, path: Path) -> None:
    deps = data.get("dependencies")
    if deps is None:
        return
    if not isinstance(deps, list):
        raise TomlParseError(
            f"{path}: 'dependencies' must be a list of strings"
        )
    for dep in deps:
        if not isinstance(dep, str):
            raise TomlParseError(
                f"{path}: each dependency must be a string, got: {dep!r}"
            )
