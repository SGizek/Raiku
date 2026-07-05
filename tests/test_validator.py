"""Tests for validator/ modules."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import tomli_w
import yaml

from validator.schema_validator import SchemaValidator, SchemaValidationError
from validator.hash_validator import HashValidator, HashMismatchError
from validator.rules_checker import RulesChecker, RulesViolationError


VALID_MANIFEST = {
    "name": "test-pkg",
    "version": "1.0.0",
    "language": "Python",
    "author": "Tester",
    "build_command": "pip install -e .",
}

VALID_VERSION = {
    "version": "1.0.0",
    "release_date": "2026-07-04",
    "stability_level": "stable",
    "changelog": ["Initial release"],
}


class TestSchemaValidator:

    def test_valid_toml_passes(self):
        SchemaValidator().validate_raiku_toml(VALID_MANIFEST)

    def test_valid_version_yml_passes(self):
        SchemaValidator().validate_version_yml(VALID_VERSION)

    def test_missing_name_raises(self):
        bad = {k: v for k, v in VALID_MANIFEST.items() if k != "name"}
        with pytest.raises(SchemaValidationError):
            SchemaValidator().validate_raiku_toml(bad)

    def test_unsupported_language_raises(self):
        bad = dict(VALID_MANIFEST, language="COBOL")
        with pytest.raises(SchemaValidationError):
            SchemaValidator().validate_raiku_toml(bad)

    def test_forbidden_build_command_raises(self):
        bad = dict(VALID_MANIFEST, build_command="rm -rf /")
        with pytest.raises(SchemaValidationError):
            SchemaValidator().validate_raiku_toml(bad)

    def test_invalid_stability_raises(self):
        bad = dict(VALID_VERSION, stability_level="legendary")
        with pytest.raises(SchemaValidationError):
            SchemaValidator().validate_version_yml(bad)


class TestHashValidator:

    def test_compute_bytes_is_sha256(self):
        data = b"hello raiku"
        expected = hashlib.sha256(data).hexdigest()
        assert HashValidator.compute_bytes(data) == expected

    def test_verify_bytes_passes_on_match(self):
        data = b"test data"
        digest = HashValidator.compute_bytes(data)
        HashValidator.verify_bytes("pkg", data, digest)  # should not raise

    def test_verify_bytes_raises_on_mismatch(self):
        with pytest.raises(HashMismatchError):
            HashValidator.verify_bytes("pkg", b"data", "a" * 64)

    def test_verify_bytes_skips_when_none(self):
        HashValidator.verify_bytes("pkg", b"anything", None)  # no raise

    def test_verify_file(self, tmp_path: Path):
        f = tmp_path / "test.toml"
        f.write_bytes(b"content")
        digest = HashValidator.compute_file(f)
        HashValidator.verify_file("pkg", f, digest)


class TestRulesChecker:

    def test_valid_package_passes(self, sample_package_dir: Path):
        manifest = VALID_MANIFEST
        violations = RulesChecker().check(sample_package_dir, manifest)
        assert violations == []

    def test_missing_src_dir_flagged(self, tmp_path: Path):
        pkg = tmp_path / "bad-pkg"
        pkg.mkdir()
        (pkg / "raiku.toml").write_bytes(b"")
        (pkg / "version.yml").write_text("")
        (pkg / "README.md").write_text("docs")
        violations = RulesChecker().check(pkg, VALID_MANIFEST)
        assert any("src" in v.lower() for v in violations)

    def test_uppercase_name_flagged(self, sample_package_dir: Path):
        bad_manifest = dict(VALID_MANIFEST, name="BadName")
        violations = RulesChecker().check(sample_package_dir, bad_manifest)
        assert any("invalid" in v.lower() or "lowercase" in v.lower() for v in violations)

    def test_assert_valid_raises_on_violations(self, tmp_path: Path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        bad_manifest = dict(VALID_MANIFEST, name="Bad Name!")
        with pytest.raises(RulesViolationError):
            RulesChecker().assert_valid(pkg, bad_manifest)
