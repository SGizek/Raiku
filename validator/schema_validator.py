"""
Raiku schema validator.

Uses Cerberus to enforce strict structural rules on raiku.toml
and version.yml fields. Schema definitions live in schemas/schema.yml.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import cerberus
import yaml

from core.constants import SUPPORTED_LANGUAGES, STABILITY_LEVELS


_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "schema.yml"


class SchemaValidationError(Exception):
    """Raised when a document fails schema validation."""

    def __init__(self, errors: dict) -> None:
        self.errors = errors
        super().__init__(self._format(errors))

    @staticmethod
    def _format(errors: dict) -> str:
        lines = ["Schema validation failed:"]
        for field, msgs in errors.items():
            for msg in (msgs if isinstance(msgs, list) else [msgs]):
                lines.append(f"  [{field}] {msg}")
        return "\n".join(lines)


class SchemaValidator:
    """Validates raiku.toml and version.yml data dicts against Cerberus schemas."""

    # ------------------------------------------------------------------
    # Cerberus schemas (defined inline; also exported to schemas/schema.yml)
    # ------------------------------------------------------------------

    RAIKU_TOML_SCHEMA: dict = {
        "name": {
            "type": "string",
            "required": True,
            "minlength": 1,
            "maxlength": 64,
            "regex": r"^[a-zA-Z0-9_\-]+$",
        },
        "version": {
            "type": "string",
            "required": True,
            "regex": r"^\d+\.\d+\.\d+.*$",
        },
        "language": {
            "type": "string",
            "required": True,
            "allowed": SUPPORTED_LANGUAGES,
        },
        "author": {
            "type": "string",
            "required": True,
            "minlength": 1,
            "maxlength": 128,
        },
        "build_command": {
            "type": "string",
            "required": True,
            "minlength": 1,
            "maxlength": 512,
        },
        "description": {
            "type": "string",
            "required": False,
            "maxlength": 512,
        },
        "license": {
            "type": "string",
            "required": False,
            "maxlength": 64,
        },
        "homepage": {
            "type": "string",
            "required": False,
            "maxlength": 256,
        },
        "dependencies": {
            "type": "list",
            "required": False,
            "schema": {"type": "string"},
        },
    }

    VERSION_YML_SCHEMA: dict = {
        "version": {
            "type": "string",
            "required": True,
            "regex": r"^\d+\.\d+\.\d+.*$",
        },
        "release_date": {
            "type": ["string", "date"],
            "required": True,
        },
        "changelog": {
            "type": ["string", "list"],
            "required": True,
        },
        "stability_level": {
            "type": "string",
            "required": True,
            "allowed": list(STABILITY_LEVELS),
        },
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_raiku_toml(self, data: dict[str, Any]) -> None:
        """
        Validate a parsed raiku.toml data dict.
        Raises SchemaValidationError on failure.
        """
        v = cerberus.Validator(self.RAIKU_TOML_SCHEMA, allow_unknown=False)
        if not v.validate(data):
            raise SchemaValidationError(v.errors)
        # Extra: forbidden build command check
        self._check_build_command(data.get("build_command", ""))

    def validate_version_yml(self, data: dict[str, Any]) -> None:
        """
        Validate a parsed version.yml data dict.
        Raises SchemaValidationError on failure.
        """
        v = cerberus.Validator(self.VERSION_YML_SCHEMA, allow_unknown=False)
        # Coerce date objects to string for Cerberus
        coerced = dict(data)
        if hasattr(coerced.get("release_date"), "isoformat"):
            coerced["release_date"] = coerced["release_date"].isoformat()
        if not v.validate(coerced):
            raise SchemaValidationError(v.errors)

    def validate_index_entry(self, entry: dict[str, Any]) -> None:
        """Validate a single package entry from index.json."""
        schema = {
            "name": {"type": "string", "required": True, "minlength": 1},
            "version": {"type": "string", "required": True},
            "language": {"type": "string", "required": True, "allowed": SUPPORTED_LANGUAGES},
            "path": {"type": "string", "required": True, "minlength": 1},
            "author": {"type": "string", "required": False},
            "description": {"type": "string", "required": False},
            "sha256": {"type": "string", "required": False},
        }
        v = cerberus.Validator(schema, allow_unknown=False)
        if not v.validate(entry):
            raise SchemaValidationError(v.errors)

    # ------------------------------------------------------------------
    # Security helpers
    # ------------------------------------------------------------------

    def _check_build_command(self, cmd: str) -> None:
        from core.constants import FORBIDDEN_BUILD_PATTERNS
        for pattern in FORBIDDEN_BUILD_PATTERNS:
            if pattern.lower() in cmd.lower():
                raise SchemaValidationError(
                    {"build_command": [f"forbidden pattern detected: '{pattern}'"]}
                )
