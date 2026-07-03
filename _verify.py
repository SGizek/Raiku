"""
Raiku verification script.
Run from the Raiku/ directory: python _verify.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PASS = []
FAIL = []

def check(label, fn):
    try:
        fn()
        PASS.append(label)
        print(f"  OK   {label}")
    except Exception as exc:
        FAIL.append((label, str(exc)))
        print(f"  FAIL {label}: {exc}")

# -----------------------------------------------------------------------
# 1. Module imports
# -----------------------------------------------------------------------
print("\n=== Module imports ===")

MODULES = [
    "core.constants", "core.config", "core.cache", "core",
    "parser.toml_parser", "parser.yaml_parser", "parser",
    "validator.schema_validator", "validator.hash_validator",
    "validator.rules_checker", "validator",
    "index.index_manager", "index",
    "installer.fetcher", "installer.cache_store",
    "installer.build_runner", "installer",
    "cli.commands.sync", "cli.commands.search",
    "cli.commands.install", "cli.commands.publish",
    "cli.commands.validate", "cli.main", "cli",
]

for m in MODULES:
    check(f"import {m}", lambda m=m: __import__(m))

# -----------------------------------------------------------------------
# 2. CLI --help (entry point smoke test)
# -----------------------------------------------------------------------
print("\n=== CLI entry point ===")

def _cli_help():
    from click.testing import CliRunner
    from cli.main import main
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0, f"exit {result.exit_code}: {result.output}"
    for cmd in ["sync", "search", "install", "publish", "validate",
                "list", "uninstall", "info", "update", "index",
                "cache", "doctor", "config", "trust"]:
        assert cmd in result.output, f"Command '{cmd}' missing from --help"

check("cli --help (all 14 commands listed)", _cli_help)

def _subcommand_helps():
    from click.testing import CliRunner
    from cli.main import main
    runner = CliRunner()
    for cmd in ["list", "uninstall", "info", "update", "doctor"]:
        r = runner.invoke(main, [cmd, "--help"])
        assert r.exit_code == 0, f"{cmd} --help failed: {r.output}"

check("all new subcommands accept --help", _subcommand_helps)

def _config_subcommands():
    from click.testing import CliRunner
    from cli.main import main
    runner = CliRunner()
    for sub in ["list", "get", "set", "reset"]:
        r = runner.invoke(main, ["config", sub, "--help"])
        assert r.exit_code == 0, f"config {sub} --help failed: {r.output}"

check("config subcommands (list/get/set/reset) --help", _config_subcommands)

def _trust_subcommands():
    from click.testing import CliRunner
    from cli.main import main
    runner = CliRunner()
    for sub in ["add", "remove", "list", "clear"]:
        r = runner.invoke(main, ["trust", sub, "--help"])
        assert r.exit_code == 0, f"trust {sub} --help failed: {r.output}"

check("trust subcommands (add/remove/list/clear) --help", _trust_subcommands)

# -----------------------------------------------------------------------
# 3. index.json structure
# -----------------------------------------------------------------------
print("\n=== index.json ===")

INDEX_PATH = Path("index/index.json")

def _index_exists():
    assert INDEX_PATH.exists(), "index/index.json missing"

def _index_valid_json():
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    assert "packages" in data
    assert len(data["packages"]) == 8

def _index_all_languages():
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    langs = {p["language"] for p in data["packages"]}
    expected = {"Python","Rust","C","CPP","Zig","Java","CSharp","Go"}
    assert langs == expected, f"Missing languages: {expected - langs}"

def _index_required_fields():
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    for pkg in data["packages"]:
        for field in ("name", "version", "language", "path"):
            assert field in pkg, f"Package {pkg.get('name')} missing '{field}'"

check("index.json exists", _index_exists)
check("index.json is valid JSON with 8 packages", _index_valid_json)
check("index.json covers all 8 languages", _index_all_languages)
check("index.json entries have required fields", _index_required_fields)

# -----------------------------------------------------------------------
# 4. Package manifests (all 8)
# -----------------------------------------------------------------------
print("\n=== Package manifests ===")

from parser.toml_parser import parse_raiku_toml
from parser.yaml_parser import parse_version_yml
from validator.schema_validator import SchemaValidator
from validator.rules_checker import RulesChecker

sv = SchemaValidator()
rc = RulesChecker()

PACKAGES = [
    ("Python",  "fast-math"),
    ("Rust",    "blazing-vec"),
    ("C",       "cmatrix"),
    ("CPP",     "geompp"),
    ("Zig",     "zigutils"),
    ("Java",    "javastream"),
    ("CSharp",  "sharputils"),
    ("Go",      "goqueue"),
]

for lang, name in PACKAGES:
    pkg_dir = Path(f"UserSub/{lang}/{name}")

    def _check_toml(d=pkg_dir, n=name):
        m = parse_raiku_toml(d)
        sv.validate_raiku_toml(m)

    def _check_yml(d=pkg_dir, n=name):
        v = parse_version_yml(d)
        sv.validate_version_yml(v)

    def _check_rules(d=pkg_dir, n=name):
        m = parse_raiku_toml(d)
        violations = rc.check(d, m)
        assert not violations, f"Rules violations: {violations}"

    check(f"{name}: raiku.toml parses + validates", _check_toml)
    check(f"{name}: version.yml parses + validates", _check_yml)
    check(f"{name}: rules check", _check_rules)

# -----------------------------------------------------------------------
# 5. Core utilities
# -----------------------------------------------------------------------
print("\n=== Core utilities ===")

def _cache_manager():
    import tempfile
    from core.cache import CacheManager
    with tempfile.TemporaryDirectory() as tmp:
        cm = CacheManager(Path(tmp))
        cm.store_file("Python", "test-pkg", "1.0.0", "raiku.toml", b"name = 'test-pkg'")
        # is_cached requires meta.json — write it before checking
        assert not cm.is_cached("Python", "test-pkg", "1.0.0"), "should be False before meta"
        cm.write_meta("Python", "test-pkg", "1.0.0", {"name": "test-pkg", "version": "1.0.0"})
        assert cm.is_cached("Python", "test-pkg", "1.0.0"), "should be True after meta"
        data = cm.get_file("Python", "test-pkg", "1.0.0", "raiku.toml")
        assert data == b"name = 'test-pkg'"
        h = CacheManager.hash_bytes(b"hello")
        assert len(h) == 64

def _hash_validator():
    from validator.hash_validator import HashValidator, HashMismatchError
    hv = HashValidator()
    data = b"raiku test"
    digest = hv.compute_bytes(data)
    assert len(digest) == 64
    hv.verify_bytes("test", data, digest)   # should not raise
    raised = False
    try:
        hv.verify_bytes("test", data, "a" * 64)
    except HashMismatchError:
        raised = True
    assert raised, "HashMismatchError not raised on bad hash"

def _forbidden_build_commands():
    from validator.schema_validator import SchemaValidator, SchemaValidationError
    sv2 = SchemaValidator()
    raised = False
    try:
        sv2._check_build_command("rm -rf /home/user")
    except SchemaValidationError:
        raised = True
    assert raised, "Forbidden pattern not caught"

def _version_consistency():
    from validator.rules_checker import RulesChecker
    # fast-math has matching versions in both files — should pass
    rc2 = RulesChecker()
    pkg_dir = Path("UserSub/Python/fast-math")
    manifest = parse_raiku_toml(pkg_dir)
    violations = rc2._check_version_consistency(pkg_dir, manifest)
    assert violations == [], f"Unexpected violations: {violations}"

check("CacheManager store/retrieve/hash", _cache_manager)
check("HashValidator verify + mismatch raises", _hash_validator)
check("Forbidden build command blocked", _forbidden_build_commands)
check("Version consistency check (fast-math)", _version_consistency)

# -----------------------------------------------------------------------
# 6. Final summary
# -----------------------------------------------------------------------
print(f"\n{'='*50}")
print(f"  PASSED: {len(PASS)}")
print(f"  FAILED: {len(FAIL)}")
if FAIL:
    print("\nFailed checks:")
    for label, err in FAIL:
        print(f"  - {label}: {err}")
    sys.exit(1)
else:
    print("\n  All checks passed. Raiku is ready.")
