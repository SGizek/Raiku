# Raiku

**Community-driven, Git-based, multi-language package ecosystem.**

Raiku is an open package manager built on GitHub. Every package lives in this repository under `UserSub/<Language>/`. Anyone can contribute. The CLI fetches only the package you need — no full repo clone required.

---

## Supported Languages

| Language | Directory     |
|----------|---------------|
| Python   | `UserSub/Python/`  |
| Rust     | `UserSub/Rust/`    |
| C        | `UserSub/C/`       |
| C++      | `UserSub/CPP/`     |
| Zig      | `UserSub/Zig/`     |
| Java     | `UserSub/Java/`    |
| C#       | `UserSub/CSharp/`  |
| Go       | `UserSub/Go/`      |

---

## Quick Start

### Install the CLI

```bash
# From source (requires Python 3.10+)
git clone https://github.com/SGizek/Raiku
cd Raiku
pip install -e .
```

### Use it

```bash
# Sync the package index
raiku sync

# Search for packages
raiku search math
raiku search queue --language Go

# Install a package
raiku install fast-math
raiku install goqueue

# Validate your package before contributing
raiku validate --dir ./my-package

# Prepare a contribution
raiku publish --dir ./my-package
```

---

## Package Structure

Every Raiku package follows this structure:

```
package-name/
  raiku.toml     ← package manifest (name, version, language, build_command, ...)
  version.yml    ← version info (version, release_date, changelog, stability_level)
  README.md      ← documentation
  src/           ← source code (at least one file)
```

### raiku.toml

```toml
name = "my-package"
version = "1.0.0"
language = "Python"
author = "Your Name"
description = "What this package does."
license = "MIT"
build_command = "pip install -e ."
dependencies = []
```

### version.yml

```yaml
version: "1.0.0"
release_date: "2026-07-03"
stability_level: stable
changelog:
  - "Initial release"
```

---

## Install Flow

When you run `raiku install <package>`, the CLI:

1. Loads `~/.raiku/index.json` (synced from this repo)
2. Finds the package path from the index
3. Validates schema compliance against `schemas/schema.yml`
4. **Fetches only the required package files** — no full repo clone
5. Caches them at `~/.raiku/cache/<language>/<name>/<version>/`
6. Verifies the SHA-256 hash against the index entry
7. Prompts you to approve the build command (safe mode)
8. Executes the build command
9. Confirms installation

---

## Security

Raiku is built with security as a first-class concern:

- **Hash validation** — every installed package is verified against its SHA-256 digest
- **Safe mode** — build commands are shown to the user before execution (default on)
- **Forbidden patterns** — dangerous shell patterns are blocked before any command runs
- **Restricted environment** — build commands run with a minimal, sandboxed environment
- **Trust flag system** — `--trust` lets you skip confirmation for known-good packages

See [`rules.md`](rules.md) for the full security policy.

---

## Contributing a Package

1. Fork this repository
2. Create your package at `UserSub/<Language>/<package-name>/`
3. Add `raiku.toml`, `version.yml`, `README.md`, and a non-empty `src/`
4. Run `raiku validate` — all checks must pass
5. Run `raiku publish` to get the index entry
6. Add your entry to `index/index.json`
7. Open a Pull Request with title `add(<language>): <package-name> v<version>`

Full contribution rules are in [`rules.md`](rules.md).

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `raiku sync` | Pull latest index from GitHub |
| `raiku search <query>` | Search the package index |
| `raiku install <package>` | Download, validate, and build a package |
| `raiku publish` | Validate and prepare a package for PR submission |
| `raiku validate` | Check package structure and schema compliance |

### Global flags

| Flag | Description |
|------|-------------|
| `--verbose` / `-v` | Enable verbose output |
| `--no-color` | Disable colored output |
| `--version` | Print CLI version |

### install flags

| Flag | Description |
|------|-------------|
| `--trust` | Skip build command confirmation |
| `--no-build` | Download and cache only, skip build |
| `--force` / `-f` | Reinstall even if already cached |

### validate flags

| Flag | Description |
|------|-------------|
| `--all` | Validate all packages in UserSub/ |
| `--language` / `-l` | Limit --all to one language |
| `--strict` | Exit non-zero if any warnings exist |

---

## Repository Layout

```
Raiku/
  UserSub/            ← all community packages
    Python/
    Rust/
    C/
    CPP/
    Zig/
    Java/
    CSharp/
    Go/
  cli/                ← Click-based CLI (5 commands)
  core/               ← config, cache manager, constants
  parser/             ← raiku.toml and version.yml parsers
  installer/          ← package fetcher, cache store, build runner
  validator/          ← schema, hash, and rules validation
  index/              ← IndexManager + index.json
  schemas/            ← schema.yml (canonical validation rules)
  docs/               ← extended documentation
  rules.md            ← package contribution rules
  pyproject.toml      ← Python project metadata + CLI entrypoint
  requirements.txt    ← pinned runtime dependencies
```

---

## Configuration

Raiku stores its state at `~/.raiku/`:

```
~/.raiku/
  config.toml     ← user configuration
  index.json      ← cached package index
  trusted.json    ← locally trusted packages
  cache/          ← installed packages
    <Language>/
      <package>/
        <version>/
```

Override settings in `~/.raiku/config.toml`:

```toml
[behaviour]
safe_mode = true      # always prompt before build (recommended)
auto_trust = false    # never silently trust packages
verbose = false

[remote]
index_url = "https://raw.githubusercontent.com/SGizek/Raiku/main/index/index.json"
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Links

- Repository: https://github.com/SGizek/Raiku
- Issues: https://github.com/SGizek/Raiku/issues
- Rules: [rules.md](rules.md)
- Schema: [schemas/schema.yml](schemas/schema.yml)
