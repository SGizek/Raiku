# Raiku Security Model

This document describes every security mechanism in Raiku and the threat model it addresses.

---

## Threat Model

Raiku is a community-driven package repository. The primary threats are:

1. **Malicious build commands** — a package contributor embeds a destructive or data-exfiltrating
   shell command in `build_command`.
2. **Package tampering** — a package's files are modified in transit or on disk after publication.
3. **Supply-chain substitution** — an attacker replaces a legitimate package with a malicious one.
4. **Runaway builds** — a build command loops indefinitely or consumes excessive resources.

---

## Defence Layers

### Layer 1 — Schema Validation (before any download)

Before any file is fetched, Raiku checks the index entry structure. Packages with
malformed metadata never reach the download stage.

### Layer 2 — Forbidden Pattern Scan (before any execution)

The full list of forbidden `build_command` patterns is checked before the command runs:

```
rm -rf          rmdir /s       del /f         format
:(){:|:&};:     dd if=         mkfs           wget http://
curl http://    > /dev/sd      chmod 777      sudo rm
DROP TABLE      __import__     exec(          eval(
os.system       subprocess.call  subprocess.Popen
```

Any match immediately aborts installation with an error. This check runs even with
`--trust` — the forbidden list cannot be bypassed.

### Layer 3 — SHA-256 Hash Verification

The `index.json` entry for each package records the SHA-256 hex digest of `raiku.toml`.
After download, Raiku recomputes the hash and compares it:

```
expected: <value from index.json>
actual:   <computed from downloaded bytes>
```

A mismatch aborts installation with a `[Security alert]` message. The cached files
are not written when a hash mismatch occurs.

### Layer 4 — Safe Mode (interactive approval)

In the default `safe_mode = true` configuration, Raiku displays the exact `build_command`
and asks the user:

```
  Build command: pip install -e .
  Run this build command for 'fast-math'? [y/N]:
```

The command is not executed until the user types `y`. This prevents silently running
commands from freshly downloaded packages.

To bypass per-install: `raiku install <pkg> --trust`  
`--trust` only skips the prompt — it does not bypass Layer 2 (forbidden patterns).

### Layer 5 — Restricted Subprocess Environment

Build commands execute in a subprocess with a minimal environment. Only these
variables are forwarded from the host:

```
PATH, HOME, USER, LOGNAME, LANG, LC_ALL, TERM,
SYSTEMROOT, WINDIR, COMSPEC, USERPROFILE, APPDATA,
LOCALAPPDATA, TEMP, TMP,
CARGO_HOME, RUSTUP_HOME, GOPATH, GOROOT,
JAVA_HOME, DOTNET_ROOT, ZIG_HOME
```

All other environment variables are stripped. This prevents secret leakage from
the host environment into the build process.

### Layer 6 — Build Timeout

Build commands are killed after **300 seconds** (5 minutes). This prevents
denial-of-service via infinite loops in build scripts.

---

## Trust Flag System

The `--trust` flag is a user-level override for safe mode only:

```bash
raiku install fast-math --trust   # skip confirmation prompt
```

Trust state is **not** persisted between commands. Every install requires an
explicit `--trust` if you want to skip the prompt.

There is no global trust list that auto-approves packages. `auto_trust = false`
is the default and is strongly recommended.

---

## What Raiku Does NOT Protect Against

- **Malicious source code** — Raiku validates structure and build commands, not the
  semantics of your source files. Review code before using it.
- **Compromised GitHub** — if the upstream repository or GitHub raw CDN is compromised,
  hash verification provides the last line of defence.
- **Side-channel attacks via build tools** — if `cargo`, `pip`, `go`, etc. are themselves
  compromised on your machine, Raiku cannot help.
- **Typosquatting** — search carefully; `fast-maths` is not `fast-math`.

---

## Reporting a Security Issue

Do not open a public issue for security vulnerabilities.

Email the maintainers directly or open a private security advisory at:
https://github.com/SGizek/Raiku/security/advisories/new

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- (Optional) suggested fix
