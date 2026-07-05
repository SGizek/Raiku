"""
Tests for parser/ modules: toml_parser, yaml_parser.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
import tomli_w

from parser.toml_parser import parse_raiku_toml, write_raiku_toml, TomlParseError
from parser.yaml_parser import parse_version_yml, write_version_yml, YamlParseError


# ===========================================================================
# TOML parser
# ===========================================================================

VALID_TOML = {
    "name": "test-pkg",
    "version": "1.0.0",
    "language": "Python",
    "author": "Test Author",
    "build_command": "pip install -e .",
}


class TestTomlParser:

    def test_parse_valid(self, tmp_path: Path):
        with open(tmp_path / "raiku.toml", "wb") as f:
            tomli_w.dump(VALID_TOML, f)
        data = parse_raiku_toml(tmp_path)
        assert data["name"] == "test-pkg"
        assert data["version"] == "1.0.0"

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(TomlParseError, match="not found"):
            parse_raiku_toml(tmp_path)

    def test_missing_required_field_raises(self, tmp_path: Path):
        bad = dict(VALID_TOML)
        del bad["author"]
        with open(tmp_path / "raiku.toml", "wb") as f:
            tomli_w.dump(bad, f)
        with pytest.raises(TomlParseError, match="author"):
            parse_raiku_toml(tmp_path)

    def test_invalid_language_raises(self, tmp_path: Path):
        bad = dict(VALID_TOML, language="COBOL")
        with open(tmp_path / "raiku.toml", "wb") as f:
            tomli_w.dump(bad, f)
        with pytest.raises(TomlParseError, match="language"):
            parse_raiku_toml(tmp_path)

    def test_invalid_name_raises(self, tmp_path: Path):
        bad = dict(VALID_TOML, name="My Package!")
        with open(tmp_path / "raiku.toml", "wb") as f:
            tomli_w.dump(bad, f)
        with pytest.raises(TomlParseError, match="invalid"):
            parse_raiku_toml(tmp_path)

    def test_invalid_version_raises(self, tmp_path: Path):
        bad = dict(VALID_TOML, version="not-semver")
        with open(tmp_path / "raiku.toml", "wb") as f:
            tomli_w.dump(bad, f)
        with pytest.raises(TomlParseError, match="semver"):
            parse_raiku_toml(tmp_path)

    def test_write_and_roundtrip(self, tmp_path: Path):
        write_raiku_toml(tmp_path, VALID_TOML)
        data = parse_raiku_toml(tmp_path)
        assert data == VALID_TOML

    def test_optional_dependencies_list(self, tmp_path: Path):
        data = dict(VALID_TOML, dependencies=["fast-math"])
        with open(tmp_path / "raiku.toml", "wb") as f:
            tomli_w.dump(data, f)
        parsed = parse_raiku_toml(tmp_path)
        assert parsed["dependencies"] == ["fast-math"]


# ===========================================================================
# YAML parser
# ===========================================================================

VALID_YML = {
    "version": "1.0.0",
    "release_date": "2026-07-04",
    "stability_level": "stable",
    "changelog": ["Initial release"],
}


class TestYamlParser:

    def test_parse_valid(self, tmp_path: Path):
        with open(tmp_path / "version.yml", "w", encoding="utf-8") as f:
            yaml.dump(VALID_YML, f, default_flow_style=False)
        data = parse_version_yml(tmp_path)
        assert data["version"] == "1.0.0"
        assert data["stability_level"] == "stable"

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(YamlParseError, match="not found"):
            parse_version_yml(tmp_path)

    def test_invalid_stability_raises(self, tmp_path: Path):
        bad = dict(VALID_YML, stability_level="legendary")
        with open(tmp_path / "version.yml", "w", encoding="utf-8") as f:
            yaml.dump(bad, f)
        with pytest.raises(YamlParseError, match="stability"):
            parse_version_yml(tmp_path)

    def test_invalid_version_raises(self, tmp_path: Path):
        bad = dict(VALID_YML, version="abc")
        with open(tmp_path / "version.yml", "w", encoding="utf-8") as f:
            yaml.dump(bad, f)
        with pytest.raises(YamlParseError, match="semver"):
            parse_version_yml(tmp_path)

    def test_changelog_as_string(self, tmp_path: Path):
        data = dict(VALID_YML, changelog="Single string changelog")
        with open(tmp_path / "version.yml", "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        parsed = parse_version_yml(tmp_path)
        assert parsed["changelog"] == "Single string changelog"

    def test_write_and_roundtrip(self, tmp_path: Path):
        write_version_yml(tmp_path, VALID_YML)
        data = parse_version_yml(tmp_path)
        assert str(data["version"]) == "1.0.0"
