"""
Raiku rules checker.

Enforces the structural filesystem rules defined in rules.md:
- Required files must exist
- src/ directory must be present
- Naming conventions
- No forbidden file types in package root
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from core.constants import REQUIRED_FILES, SRC_DIR, RAIKU_TOML, VERSION_YML, README_MD


class RulesViolationError(Exception):
    """Raised when a package directory violates structural rules."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__(
            "Package rules violations:\n" +
            "\n".join(f"  - {v}" for v in violations)
        )


# File extensions that are never allowed in a package root
_FORBIDDEN_EXTENSIONS: frozenset[str] = frozenset({
    ".exe", ".dll", ".so", ".dylib",  # Pre-compiled binaries
    ".sh",                             # Shell scripts in root (must be in src/)
    ".bat", ".cmd", ".ps1",            # Windows scripts in root
    ".key", ".pem", ".p12", ".pfx",   # Credentials
    ".env",                            # Environment files
})

# Maximum allowed package name length
_MAX_NAME_LENGTH: int = 64

# Valid package name pattern
_NAME_PATTERN: re.Pattern = re.compile(r"^[a-z][a-z0-9_\-]*$")


class RulesChecker:
    """Check a package directory against Raiku structural rules."""

    def check(self, package_dir: Path, manifest: dict[str, Any]) -> list[str]:
        """
        Run all rule checks on *package_dir*.

        Returns a (possibly empty) list of violation strings.
        Does NOT raise — callers decide how to handle violations.
        """
        violations: list[str] = []

        violations.extend(self._check_required_files(package_dir))
        violations.extend(self._check_src_dir(package_dir))
        violations.extend(self._check_forbidden_files(package_dir))
        violations.extend(self._check_name(manifest))
        violations.extend(self._check_version_consistency(package_dir, manifest))

        return violations

    def assert_valid(self, package_dir: Path, manifest: dict[str, Any]) -> None:
        """
        Run all checks and raise RulesViolationError if any violations found.
        """
        violations = self.check(package_dir, manifest)
        if violations:
            raise RulesViolationError(violations)

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_required_files(self, package_dir: Path) -> list[str]:
        violations = []
        for fname in REQUIRED_FILES:
            target = package_dir / fname
            if not target.exists():
                violations.append(
                    f"Missing required {'directory' if fname == SRC_DIR else 'file'}: {fname}"
                )
        return violations

    def _check_src_dir(self, package_dir: Path) -> list[str]:
        src = package_dir / SRC_DIR
        if src.exists() and not src.is_dir():
            return [f"'src' must be a directory, not a file"]
        if src.exists() and src.is_dir():
            # src/ must contain at least one file
            contents = list(src.iterdir())
            if not contents:
                return ["'src/' directory is empty — package must contain source files"]
        return []

    def _check_forbidden_files(self, package_dir: Path) -> list[str]:
        violations = []
        for item in package_dir.iterdir():
            if item.is_file() and item.suffix.lower() in _FORBIDDEN_EXTENSIONS:
                violations.append(
                    f"Forbidden file type in package root: {item.name} "
                    f"(extension '{item.suffix}' not allowed)"
                )
        return violations

    def _check_name(self, manifest: dict[str, Any]) -> list[str]:
        name = manifest.get("name", "")
        violations = []
        if not name:
            violations.append("Package 'name' is missing or empty")
            return violations
        if len(name) > _MAX_NAME_LENGTH:
            violations.append(
                f"Package name '{name}' exceeds maximum length of {_MAX_NAME_LENGTH}"
            )
        if not _NAME_PATTERN.match(name):
            violations.append(
                f"Package name '{name}' is invalid. "
                "Names must be lowercase, start with a letter, "
                "and contain only letters, digits, hyphens, and underscores."
            )
        return violations

    def _check_version_consistency(
        self, package_dir: Path, manifest: dict[str, Any]
    ) -> list[str]:
        """Ensure raiku.toml version matches version.yml version."""
        toml_version = manifest.get("version", "")
        version_yml = package_dir / VERSION_YML
        if not version_yml.exists():
            return []  # Already flagged by required-files check

        try:
            import yaml
            with open(version_yml, "r", encoding="utf-8") as fh:
                yml_data = yaml.safe_load(fh)
            yml_version = str(yml_data.get("version", ""))
        except Exception:
            return ["Could not read version.yml for consistency check"]

        if toml_version and yml_version and toml_version != yml_version:
            return [
                f"Version mismatch: raiku.toml says '{toml_version}', "
                f"version.yml says '{yml_version}'"
            ]
        return []
