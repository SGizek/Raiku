# Raiku

**Community-driven, Git-based, multi-language package ecosystem.**

Raiku is an open package manager built on GitHub. Every package lives in this repository under `UserSub/<Language>/`. Anyone can contribute. The CLI fetches only the package you need — no full repo clone required.

---

## Supported Languages

| Language | Directory          |
|----------|--------------------|
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
# Requires Python 3.10+
git clone https://github.com/SGizek/Raiku
cd Raiku
pip install -e .
```

### First steps

```bash
# Pull the latest package index
raiku sync

# Search for packages
raiku search math
raiku search queue --language Go
raiku search utils --tag collections

# Install a package
raiku install fast-math
raiku install goqueue

# See what's installed
raiku list

# Check for updates
raiku outdated
raiku update --all

# Scaffold a new package
raiku init

# Validate and publish your package
raiku validate --dir ./my-package
raiku publish  --dir ./my-package
```

---

## All Commands

| Command | Description |
|---------|-------------|
| `raiku sync` | Pull latest index from GitHub |
| `raiku search <query>` | Search by name, description, author, or `--tag` |
| `raiku install <package>` | Install from index with dep resolution + progress bars |
| `raiku install ./path` | Install directly from a local directory |
| `raiku init` | Interactive wizard — scaffold a new package |
| `raiku info <package>` | Full package details and local install status |
| `raiku list` | All locally installed packages |
| `raiku outdated` | Packages that have newer versions available |
| `raiku update <package>` | Update one package |
| `raiku update --all` | Update everything (respects pins) |
| `raiku uninstall <package>` | Remove from local cache |
| `raiku audit` | Verify cached package hashes against the index |
| `raiku stats` | Ecosystem + local cache statistics |
| `raiku pin add <package>` | Pin a package at its current version |
| `raiku pin remove <package>` | Unpin a package |
| `raiku pin list` | Show all pinned packages |
| `raiku publish` | Validate and prepare a package for PR submission |
| `raiku validate` | Check package structure and schema compliance |
| `raiku index --rebuild` | Auto-regenerate index.json from UserSub/ |
| `raiku index --stats` | Package count, language breakdown |
| `raiku index --check` | Verify every index entry path and hash |
| `raiku cache --info` | Disk usage and installed package count |
| `raiku cache --clear` | Wipe the entire local cache |
| `raiku doctor` | Check that build tools (gcc, cargo, go, …) are installed |
| `raiku config list` | View all configuration values |
| `raiku config get <key>` | Print one config value |
| `raiku config set <key> <value>` | Update a config value |
| `raiku config reset` | Reset configuration to defaults |
| `raiku trust add <package>` | Persistently trust a package's build command |
| `raiku trust remove <package>` | Revoke trust |
| `raiku trust list` | Show trusted packages |
| `raiku completion <shell>` | Generate shell completions (bash/zsh/fish/PowerShell) |

---

## Package Structure

Every Raiku package follows this layout:

```
package-name/
  raiku.toml     ← manifest (name, version, language, build_command, …)
  version.yml    ← version info (version, release_date, changelog, stability_level)
  README.md      ← documentation
  src/           ← source code (at least one file required)
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
tags = ["utils", "math"]
dependencies = []
```

### version.yml

```yaml
version: "1.0.0"
release_date: "2026-07-04"
stability_level: stable
changelog:
  - "Initial release"
```

---

## Install Flow

When you run `raiku install <package>`:

1. Loads `~/.raiku/index.json` (synced from this repo)
2. Resolves transitive dependencies and installs them first
3. Fetches only the required package files — **no full repo clone**
4. Shows real-time download progress
5. Validates schema compliance against `schemas/schema.yml`
6. Verifies the SHA-256 hash against the index entry
7. Caches files at `~/.raiku/cache/<language>/<name>/<version>/`
8. Prompts you to approve the build command (safe mode, default on)
9. Executes the build command in a restricted subprocess environment
10. Optionally updates `raiku.lock`

---

## Creating a Package

The fastest way is `raiku init` — an interactive wizard that generates all required files:

```bash
raiku init
# answers a few prompts → creates package-name/ with raiku.toml, version.yml, README.md, src/
```

Or scaffold for a specific language directly:

```bash
raiku init my-lib --language Rust --yes
```

Supported languages and what gets generated in `src/`:

| Language | Generated files |
|----------|----------------|
| Python   | `<name>.py`, `pyproject.toml` |
| Rust     | `lib.rs`, `Cargo.toml` |
| C        | `<name>.c`, `<name>.h` |
| C++      | `<name>.hpp`, `<name>.cpp`, `CMakeLists.txt` |
| Zig      | `<name>.zig`, `build.zig` |
| Java     | `dev/raiku/<name>/<Name>.java` |
| C#       | `<Name>.cs`, `<name>.csproj` |
| Go       | `<name>.go`, `<name>_test.go`, `go.mod` |

---

## Contributing a Package

1. Run `raiku init` to scaffold the package
2. Add your source code to `src/`
3. Run `raiku validate --dir ./my-package` — all checks must pass
4. Run `raiku publish --dir ./my-package` — generates the index entry and PR instructions
5. Fork the repo, add your package under `UserSub/<Language>/`
6. Paste the index entry into `index/index.json`
7. Open a Pull Request: `add(<Language>): my-package v1.0.0`

Full rules are in [`rules.md`](rules.md). Full format spec is in [`docs/package-format.md`](docs/package-format.md).

---

## Security

- **Hash validation** — SHA-256 of every package verified at install time
- **Safe mode** — build commands shown and approved by user before execution (default on)
- **Forbidden pattern scan** — dangerous shell patterns blocked before any command runs
- **Persistent trust** — `raiku trust add <pkg>` to skip prompts for known-good packages
- **Audit** — `raiku audit` verifies all cached packages haven't been tampered with
- **Restricted subprocess** — build commands run with a stripped-down environment
- **Build timeout** — 300-second hard limit on all build commands
- **Pins** — `raiku pin add <pkg>` prevents accidental updates to stable installs

See [`docs/security.md`](docs/security.md) for the full security model.

---

## Lock File

Run `raiku install <pkg> --lock` to record exact installed versions in `raiku.lock`:

```json
{
  "lock_version": "1",
  "packages": {
    "fast-math": { "version": "1.0.0", "language": "Python", "sha256": "..." }
  }
}
```

Commit `raiku.lock` alongside your project to ensure reproducible installs across machines.

---

## Shell Completions

```bash
raiku completion bash   --install   # appends to ~/.bashrc
raiku completion zsh    --install   # appends to ~/.zshrc
raiku completion fish   --install   # writes ~/.config/fish/completions/raiku.fish
raiku completion powershell --install
```

Or print the script and add it manually:

```bash
raiku completion bash >> ~/.bashrc
```

---

## Configuration

Raiku stores state at `~/.raiku/`:

```
~/.raiku/
  config.toml     ← user configuration
  index.json      ← cached package index
  trusted.json    ← persistently trusted packages
  pins.json       ← pinned package versions
  cache/          ← installed packages
    <Language>/
      <package>/
        <version>/
```

Edit settings without touching the file:

```bash
raiku config list                    # view all values
raiku config set safe_mode false     # disable build confirmation
raiku config set verbose true        # enable verbose output
raiku config reset                   # restore all defaults
```

Or edit `~/.raiku/config.toml` directly:

```toml
[behaviour]
safe_mode = true      # always prompt before build (recommended)
auto_trust = false    # never silently trust packages
verbose = false

[remote]
index_url = "https://raw.githubusercontent.com/SGizek/Raiku/main/index/index.json"
```

---

## Repository Layout

```
Raiku/
  UserSub/              ← all community packages
    Python/
    Rust/
    C/
    CPP/
    Zig/
    Java/
    CSharp/
    Go/
  cli/                  ← Click CLI — 20 commands
    commands/           ← one file per command
  core/                 ← config, cache, constants, resolver, lockfile, pins, trust, templates
  parser/               ← raiku.toml and version.yml parsers
  installer/            ← package fetcher (streaming), cache store, safe build runner
  validator/            ← schema (Cerberus), hash (SHA-256), rules checker
  index/                ← IndexManager + index.json
  schemas/              ← schema.yml (canonical validation rules)
  docs/                 ← extended documentation
  rules.md              ← strict package contribution rulebook
  pyproject.toml        ← Python project metadata and CLI entrypoint
  requirements.txt      ← pinned runtime dependencies
  _verify.py            ← self-contained test suite (60 checks)
  _smoke_new.py         ← feature smoke tests (18 checks)
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Links

- Repository: https://github.com/SGizek/Raiku
- Issues: https://github.com/SGizek/Raiku/issues
- CLI Reference: [docs/cli-reference.md](docs/cli-reference.md)
- Package Format: [docs/package-format.md](docs/package-format.md)
- Security Model: [docs/security.md](docs/security.md)
- Contributing: [docs/contributing.md](docs/contributing.md)
- Rules: [rules.md](rules.md)
- Schema: [schemas/schema.yml](schemas/schema.yml)
