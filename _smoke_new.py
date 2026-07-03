"""Smoke tests for all batch-2 new commands and core modules."""
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

# --- New command --help checks ---
print("\n=== New command --help ===")
NEW_CMDS = ["init", "outdated", "stats", "audit", "completion"]
for cmd in NEW_CMDS:
    def _h(c=cmd):
        r = runner.invoke(main, [c, "--help"])
        assert r.exit_code == 0, r.output
    check(f"{cmd} --help", _h)

PIN_SUBS = ["add", "remove", "list"]
for sub in PIN_SUBS:
    def _p(s=sub):
        r = runner.invoke(main, ["pin", s, "--help"])
        assert r.exit_code == 0, r.output
    check(f"pin {sub} --help", _p)

# --- init dry run ---
print("\n=== raiku init ===")
def _init_creates_files():
    with tempfile.TemporaryDirectory() as tmp:
        r = runner.invoke(main, [
            "init", "test-pkg",
            "--language", "Python",
            "--output-dir", tmp,
            "--yes",
        ])
        assert r.exit_code == 0, r.output
        pkg = Path(tmp) / "test-pkg"
        assert (pkg / "raiku.toml").exists()
        assert (pkg / "version.yml").exists()
        assert (pkg / "README.md").exists()
        assert (pkg / "src").is_dir()
        assert any((pkg / "src").iterdir())
check("init creates all required files (Python)", _init_creates_files)

def _init_rust():
    with tempfile.TemporaryDirectory() as tmp:
        r = runner.invoke(main, ["init", "my-lib", "--language", "Rust", "--output-dir", tmp, "--yes"])
        assert r.exit_code == 0, r.output
        assert (Path(tmp) / "my-lib" / "src" / "lib.rs").exists()
check("init creates src/lib.rs for Rust", _init_rust)

def _init_all_languages():
    import core.constants as c
    with tempfile.TemporaryDirectory() as tmp:
        for lang in c.SUPPORTED_LANGUAGES:
            r = runner.invoke(main, ["init", f"pkg-{lang.lower()}", "--language", lang,
                                     "--output-dir", tmp, "--yes"])
            assert r.exit_code == 0, f"{lang}: {r.output}"
            assert (Path(tmp) / f"pkg-{lang.lower()}" / "raiku.toml").exists()
check("init works for all 8 languages", _init_all_languages)

# --- LockFile ---
print("\n=== LockFile ===")
def _lockfile():
    from core.lockfile import LockFile
    with tempfile.NamedTemporaryFile(suffix=".lock", delete=False) as f:
        path = Path(f.name)
    path.unlink()
    lf = LockFile(path)
    lf.add({"name": "fast-math", "version": "1.0.0", "language": "Python",
             "path": "UserSub/Python/fast-math", "sha256": "abc"})
    assert lf.is_locked("fast-math")
    assert lf.locked_version("fast-math") == "1.0.0"
    lf.remove("fast-math")
    assert not lf.is_locked("fast-math")
    if path.exists(): path.unlink()
check("LockFile add/check/remove", _lockfile)

# --- PinManager ---
print("\n=== PinManager ===")
def _pins():
    from core.pins import PinManager
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    path.unlink()
    pm = PinManager(path)
    assert not pm.is_pinned("goqueue")
    pm.pin("goqueue", "1.0.0", reason="stability")
    assert pm.is_pinned("goqueue")
    assert pm.pinned_version("goqueue") == "1.0.0"
    assert len(pm.list_pins()) == 1
    pm.unpin("goqueue")
    assert not pm.is_pinned("goqueue")
    if path.exists(): path.unlink()
check("PinManager pin/check/unpin", _pins)

# --- DependencyResolver ---
print("\n=== DependencyResolver ===")
def _resolver_no_deps():
    from core.resolver import DependencyResolver
    from index.index_manager import IndexManager
    manager = IndexManager()
    manager._data = {
        "schema_version": "1.0.0",
        "packages": [
            {"name": "fast-math", "version": "1.0.0", "language": "Python",
             "path": "UserSub/Python/fast-math", "dependencies": []},
        ]
    }
    resolver = DependencyResolver(manager)
    order = resolver.resolve("fast-math")
    assert order == ["fast-math"]
check("DependencyResolver resolves single package with no deps", _resolver_no_deps)

def _resolver_with_deps():
    from core.resolver import DependencyResolver
    from index.index_manager import IndexManager
    manager = IndexManager()
    manager._data = {
        "schema_version": "1.0.0",
        "packages": [
            {"name": "a", "version": "1.0.0", "language": "Python", "path": "x", "dependencies": ["b"]},
            {"name": "b", "version": "1.0.0", "language": "Python", "path": "y", "dependencies": []},
        ]
    }
    resolver = DependencyResolver(manager)
    order = resolver.resolve("a")
    assert order.index("b") < order.index("a"), f"b must come before a, got {order}"
check("DependencyResolver installs deps before root", _resolver_with_deps)

def _resolver_circular():
    from core.resolver import DependencyResolver, DependencyError
    from index.index_manager import IndexManager
    manager = IndexManager()
    manager._data = {
        "schema_version": "1.0.0",
        "packages": [
            {"name": "x", "version": "1.0.0", "language": "Python", "path": "x", "dependencies": ["y"]},
            {"name": "y", "version": "1.0.0", "language": "Python", "path": "y", "dependencies": ["x"]},
        ]
    }
    resolver = DependencyResolver(manager)
    raised = False
    try:
        resolver.resolve("x")
    except DependencyError:
        raised = True
    assert raised
check("DependencyResolver detects circular dependency", _resolver_circular)

# --- Templates ---
print("\n=== Templates ===")
def _all_templates_have_src_files():
    from core.templates import TEMPLATES
    for lang, tmpl in TEMPLATES.items():
        assert tmpl.src_files, f"{lang} template has no src_files"
        assert tmpl.default_build_command, f"{lang} has no build command"
check("All 8 language templates have src files and build commands", _all_templates_have_src_files)

# --- Completion ---
print("\n=== Shell completion ===")
def _completion_scripts():
    from cli.commands.completion import _generate
    for shell in ("bash", "zsh", "fish", "powershell"):
        script, config = _generate(shell)
        assert script, f"No completion script for {shell}"
        assert config, f"No config path for {shell}"
check("Completion scripts generated for all 4 shells", _completion_scripts)

# --- Summary ---
print(f"\n{'='*50}")
print(f"  PASSED: {len(PASS)}")
print(f"  FAILED: {len(FAIL)}")
if FAIL:
    for label, err in FAIL:
        print(f"  - {label}: {err}")
    sys.exit(1)
else:
    print(f"\n  All {len(PASS)} new feature checks passed.")
