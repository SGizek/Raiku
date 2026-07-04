"""Smoke tests for all batch-3 commands."""
import sys, tempfile, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from click.testing import CliRunner
from cli.main import main

runner = CliRunner()
PASS, FAIL = [], []

def check(label, fn):
    try:
        fn()
        PASS.append(label)
        print(f"  OK   {label}")
    except Exception as exc:
        FAIL.append((label, str(exc)))
        print(f"  FAIL {label}: {exc}")

print("\n=== Batch 3 command --help checks ===")
CMDS = [
    "run", "from-lock", "diff", "test", "why",
    "graph", "export", "import", "verify", "rollback",
    "login", "whoami", "logout",
]
for cmd in CMDS:
    def _h(c=cmd):
        r = runner.invoke(main, [c, "--help"])
        assert r.exit_code == 0, f"exit {r.exit_code}: {r.output}"
    check(f"{cmd} --help", _h)

print("\n=== search --sort ===")
def _search_sort():
    r = runner.invoke(main, ["search", "math", "--sort", "latest"])
    # Will fail with no index but should not crash with unrecognised option
    assert "--sort" not in r.output or r.exit_code in (0, 1)
check("search accepts --sort flag", _search_sort)

print("\n=== info --changelog ===")
def _info_changelog():
    r = runner.invoke(main, ["info", "fast-math", "--changelog", "--help"])
    assert r.exit_code == 0
    assert "--changelog" in r.output
check("info --changelog flag present", _info_changelog)

print("\n=== publish --submit flag ===")
def _publish_submit():
    r = runner.invoke(main, ["publish", "--help"])
    assert r.exit_code == 0
    assert "--submit" in r.output
check("publish --submit flag present", _publish_submit)

print("\n=== from-lock ===")
def _from_lock_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        r = runner.invoke(main, ["from-lock", "--file", str(Path(tmp) / "raiku.lock")])
        assert r.exit_code != 0  # should fail — file doesn't exist
check("from-lock exits non-zero on missing lock file", _from_lock_missing_file)

def _from_lock_empty():
    with tempfile.TemporaryDirectory() as tmp:
        lock_path = Path(tmp) / "raiku.lock"
        lock_path.write_text(
            '{"lock_version":"1","generated_at":0,"packages":{}}',
            encoding="utf-8"
        )
        r = runner.invoke(main, ["from-lock", "--file", str(lock_path)])
        assert "empty" in r.output.lower() or r.exit_code == 0
check("from-lock reports empty lock file gracefully", _from_lock_empty)

print("\n=== export / import ===")
def _export_no_packages():
    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "req.raiku")
        r = runner.invoke(main, ["export", "--output", out])
        # No packages installed in test env — should just report empty
        assert r.exit_code == 0
check("export handles empty cache gracefully", _export_no_packages)

def _import_missing_file():
    r = runner.invoke(main, ["import", "--file", "nonexistent.raiku"])
    assert r.exit_code != 0
check("import exits non-zero on missing file", _import_missing_file)

print("\n=== rollback ===")
def _rollback_not_installed():
    r = runner.invoke(main, ["rollback", "nonexistent-package-xyz"])
    assert r.exit_code != 0
check("rollback exits non-zero for uninstalled package", _rollback_not_installed)

print("\n=== verify ===")
def _verify_not_installed():
    r = runner.invoke(main, ["verify", "nonexistent-package-xyz"])
    assert r.exit_code != 0
check("verify exits non-zero for uninstalled package", _verify_not_installed)

print("\n=== readonly config ===")
def _readonly_field():
    from core.config import RaikuConfig
    cfg = RaikuConfig()
    assert hasattr(cfg, "readonly")
    assert cfg.readonly is False
    cfg.readonly = True
    assert cfg.readonly is True
check("RaikuConfig has readonly field defaulting to False", _readonly_field)

print("\n=== login / whoami / logout ===")
def _whoami_not_logged_in():
    r = runner.invoke(main, ["whoami"])
    assert r.exit_code == 0
    assert "not logged in" in r.output.lower() or "unknown" in r.output.lower() or "logged in" in r.output.lower()
check("whoami runs without crash", _whoami_not_logged_in)

print("\n=== resumable fetcher ===")
def _resumable_method_exists():
    from installer.fetcher import PackageFetcher
    f = PackageFetcher()
    assert hasattr(f, "_get_resumable"), "PackageFetcher missing _get_resumable"
check("PackageFetcher has _get_resumable method", _resumable_method_exists)

print(f"\n{'='*50}")
print(f"  PASSED: {len(PASS)}")
print(f"  FAILED: {len(FAIL)}")
if FAIL:
    for label, err in FAIL:
        print(f"  - {label}: {err}")
    sys.exit(1)
else:
    print(f"\n  All {len(PASS)} batch-3 checks passed.")
