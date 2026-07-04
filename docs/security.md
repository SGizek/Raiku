# Raiku Security Model

This document describes every security mechanism in Raiku and the threat model each one addresses.

---

## Threat Model

Raiku is a community-driven package repository. Primary threats:

1. **Malicious build commands** — a contributor embeds a destructive or data-exfiltrating shell command in `build_command`.
2. **Package tampering** — a package's files are modified in transit or after installation on disk.
3. **Supply-chain substitution** — an attacker replaces a legitimate package with a malicious one.
4. **Runaway builds** — a build command loops indefinitely or consumes excessive resources.
5. **Post-install corruption** — a cached package is silently altered after being verified.

---

## Defence Layers

### Layer 1 — Schema Validation (before any download)

Before any file is fetched, Raiku checks the index entry structure using Cerberus schema validation. Packages with malformed metadata never reach the download stage.

### Layer 2 — Forbidden Pattern Scan (before any execution)

The full list of forbidden `build_command` patterns is checked before the command runs:

```
rm -rf          rmdir /s       del /f         format
:(){:|:&};:     dd if=         mkfs           wget http://
curl http://    > /dev/sd      chmod 777      sudo rm
DROP TABLE      __import__     exec(          eval(
os.system       subprocess.call  subprocess.Popen
```

Any match immediately aborts installation with an error. **This check runs even with `--trust`** — the forbidden list cannot be bypassed by any flag.

### Layer 3 — SHA-256 Hash Verification (integrity at download)

`index.json` records the SHA-256 hex digest of each package's `raiku.toml`. After download, Raiku recomputes and compares:

```
expected : <value from index.json>
actual   : <computed from downloaded bytes>
```

A mismatch aborts installation with a `[Security alert]` message. Files are not written to cache when a mismatch occurs.

### Layer 4 — Post-Install Audit (integrity at rest)

Run `raiku audit` at any time to re-verify all cached packages:

```bash
raiku audit        # verify all packages
raiku audit --fix  # evict any that fail
```

This catches tampering that occurs after the initial install. Evicted packages can be cleanly reinstalled from the index.

### Layer 5 — Safe Mode (interactive approval)

In the default `safe_mode = true` configuration, Raiku shows the exact `build_command` before running it:

```
  Build command: pip install -e .
  Run this build command for 'fast-math'? [y/N]:
```

The command does not execute until the user types `y`. Applies to both remote and local installs.

To skip per-install: `raiku install <pkg> --trust`

`--trust` only skips the prompt — it does not bypass Layer 2 (forbidden patterns).

### Layer 6 — Persistent Trust System

Rather than passing `--trust` every time, you can explicitly mark a package as trusted after reviewing it:

```bash
raiku trust add fast-math --reason "reviewed source, MIT license"
```

Trusted packages skip the confirmation prompt automatically on future installs. Trust is stored at `~/.raiku/trusted.json` and is always an **explicit, per-machine user decision** — never automatic.

```bash
raiku trust list          # show trusted packages
raiku trust remove <pkg>  # revoke trust
raiku trust clear         # revoke all trust
```

### Layer 7 — Restricted Subprocess Environment

Build commands execute in a subprocess with a stripped-down environment. Only these variables are forwarded from the host:

```
PATH, HOME, USER, LOGNAME, LANG, LC_ALL, TERM
SYSTEMROOT, WINDIR, COMSPEC, USERPROFILE, APPDATA, LOCALAPPDATA, TEMP, TMP
CARGO_HOME, RUSTUP_HOME, GOPATH, GOROOT, JAVA_HOME, DOTNET_ROOT, ZIG_HOME
```

All other environment variables — including secrets, API keys, and session tokens — are stripped. This prevents accidental leakage into build subprocesses.

### Layer 8 — Build Timeout

Build commands are killed after **300 seconds** (5 minutes). This prevents runaway builds from hanging indefinitely or consuming excessive CPU/memory.

### Layer 9 — Pin System

Prevent automatic updates from overwriting known-good installs:

```bash
raiku pin add fast-math --reason "stable baseline for production"
```

Pinned packages are skipped by `raiku update --all`. They can only be updated with an explicit `raiku install fast-math --force`.

---

## Configuration Security Defaults

| Setting | Default | Meaning |
|---------|---------|---------|
| `safe_mode` | `true` | Always prompt before build |
| `auto_trust` | `false` | Never silently trust packages |

Changing `safe_mode = false` or `auto_trust = true` is strongly discouraged unless you are operating in a fully trusted, isolated environment.

```bash
raiku config set safe_mode false    # WARNING: disables build confirmation
raiku config set auto_trust true    # WARNING: silently runs all build commands
```

Both settings show a visible warning when changed.

---

## What Raiku Does NOT Protect Against

- **Malicious source code** — Raiku validates structure and build commands, not the semantics of your source files. Read the code before using it.
- **Compromised GitHub** — if the upstream repository or GitHub's raw CDN is compromised, SHA-256 hash verification provides the last line of defence.
- **Compromised build tools** — if `cargo`, `pip`, `go`, `javac`, etc. are compromised on your machine, Raiku cannot detect it.
- **Typosquatting** — `fast-maths` is not `fast-math`. Always verify the package name before installing.

---

## Reporting a Security Issue

Do not open a public issue for security vulnerabilities.

Open a private security advisory at:  
https://github.com/SGizek/Raiku/security/advisories/new

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- (Optional) suggested fix
