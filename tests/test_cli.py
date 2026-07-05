"""CLI smoke tests — every command must accept --help and exit 0."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import main


ALL_COMMANDS = [
    "sync", "search", "install", "publish", "validate",
    "list", "uninstall", "info", "update", "index",
    "cache", "doctor", "config", "trust",
    "init", "outdated", "stats", "pin", "audit", "completion",
    "run", "from-lock", "diff", "test", "why", "graph",
    "export", "import", "verify", "rollback",
    "login", "whoami", "logout",
]

SUBCOMMANDS = {
    "config":  ["list", "get", "set", "reset"],
    "trust":   ["add", "remove", "list", "clear"],
    "pin":     ["add", "remove", "list"],
    "index":   [],
    "cache":   [],
}


@pytest.mark.parametrize("cmd", ALL_COMMANDS)
def test_help(cmd: str):
    runner = CliRunner()
    result = runner.invoke(main, [cmd, "--help"])
    assert result.exit_code == 0, f"{cmd} --help failed:\n{result.output}"


@pytest.mark.parametrize("group,sub", [
    (g, s)
    for g, subs in SUBCOMMANDS.items()
    for s in subs
])
def test_subcommand_help(group: str, sub: str):
    runner = CliRunner()
    result = runner.invoke(main, [group, sub, "--help"])
    assert result.exit_code == 0, f"{group} {sub} --help failed:\n{result.output}"


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "raiku" in result.output.lower() or "1." in result.output


def test_init_creates_package(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "init", "my-new-pkg",
        "--language", "Python",
        "--output-dir", str(tmp_path),
        "--yes",
    ])
    assert result.exit_code == 0, result.output
    pkg = tmp_path / "my-new-pkg"
    assert (pkg / "raiku.toml").exists()
    assert (pkg / "version.yml").exists()
    assert (pkg / "README.md").exists()
    assert (pkg / "src").is_dir()


def test_validate_good_package(sample_package_dir: Path):
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--dir", str(sample_package_dir)])
    assert result.exit_code == 0, result.output
    assert "PASSED" in result.output or "passed" in result.output.lower()


def test_validate_missing_src_fails(tmp_path: Path):
    import tomli_w, yaml
    pkg = tmp_path / "bad-pkg"
    pkg.mkdir()
    with open(pkg / "raiku.toml", "wb") as f:
        tomli_w.dump({
            "name": "bad-pkg", "version": "1.0.0", "language": "Python",
            "author": "X", "build_command": "echo hi",
        }, f)
    with open(pkg / "version.yml", "w") as f:
        yaml.dump({"version": "1.0.0", "release_date": "2026-07-04",
                   "stability_level": "stable", "changelog": ["init"]}, f)
    (pkg / "README.md").write_text("docs")
    # No src/ dir
    result = runner.invoke(main, ["validate", "--dir", str(pkg)])
    assert result.exit_code != 0 or "error" in result.output.lower() or "fail" in result.output.lower()


def test_list_no_packages(raiku_config):
    runner = CliRunner()
    result = runner.invoke(main, ["--no-color", "list"])
    assert result.exit_code == 0


def test_from_lock_missing_file():
    runner = CliRunner()
    result = runner.invoke(main, ["from-lock", "--file", "/nonexistent/raiku.lock"])
    assert result.exit_code != 0


def test_export_empty_cache():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmp:
        result = runner.invoke(main, ["export", "--output", str(Path(tmp) / "req.raiku")])
        assert result.exit_code == 0


# Need runner fixture at module level for test_validate_missing_src_fails
runner = CliRunner()
