# Contributing to Raiku

Welcome. This guide covers adding a new package, updating an existing one, and what happens during review.

---

## Before You Start

1. Read [`rules.md`](../rules.md) — it is enforced strictly by CI and by reviewers.
2. Install the Raiku CLI from the repo root:
   ```bash
   pip install -e .
   raiku --version
   ```
3. Sync the index so `raiku validate` can resolve dependency names:
   ```bash
   raiku sync
   ```

---

## Adding a New Package

### Option A — Use the init wizard (recommended)

```bash
raiku init
```

The wizard prompts for name, language, version, author, description, license, build command, and tags. It generates all required files and the correct `src/` layout for your language.

```bash
# Non-interactive with defaults
raiku init my-lib --language Rust --yes
```

Then fill in your actual source code in `src/`, and jump to Step 5 below.

---

### Option B — Create files manually

#### Step 1 — Create the directory structure

```
UserSub/<Language>/<your-package-name>/
  raiku.toml
  version.yml
  README.md
  src/
    <your source files>
```

Replace `<Language>` with one of: `Python`, `Rust`, `C`, `CPP`, `Zig`, `Java`, `CSharp`, `Go`.

#### Step 2 — Write raiku.toml

```toml
name = "your-package-name"
version = "1.0.0"
language = "Python"
author = "Your Name"
description = "One sentence about what this does."
license = "MIT"
build_command = "pip install -e ."
tags = ["utils", "math"]       # optional but recommended
dependencies = []              # list of other Raiku package names
```

#### Step 3 — Write version.yml

```yaml
version: "1.0.0"          # must match raiku.toml exactly
release_date: "2026-07-04"
stability_level: stable
changelog:
  - "Initial release"
```

#### Step 4 — Write README.md

Your README must contain at minimum:
- What the package does (1–2 sentences)
- `raiku install <name>` install command
- A basic usage example

---

### Step 5 — Validate

```bash
raiku validate --dir UserSub/<Language>/your-package-name
```

All checks must pass with zero errors. Fix any issues before continuing.

### Step 6 — Generate the index entry

```bash
raiku publish --dir UserSub/<Language>/your-package-name
```

This prints the exact JSON block to add to `index/index.json`, including the computed SHA-256 hash. Copy and paste it into `index/index.json` inside the `"packages"` array.

### Step 7 — Verify the index is consistent

```bash
raiku index --check --root .
```

Should show all entries as valid.

### Step 8 — Open a Pull Request

Fork the repo, push your branch, open a PR:

- **Title**: `add(<Language>): your-package-name v1.0.0`
- **Branch name**: `add/<language>/your-package-name`
- **Body**: include the output of `raiku validate` and a description

---

## Updating an Existing Package

1. Bump `version` in **both** `raiku.toml` and `version.yml` — they must match, and must be higher than the current published version.
2. Add a new entry to `changelog` in `version.yml` describing what changed.
3. Run `raiku publish --dir UserSub/<Language>/package-name` to get the new SHA-256.
4. Update the `version` and `sha256` fields for your package in `index/index.json`.
5. Open a PR with title: `update(<Language>): package-name v<new-version>`

---

## Dependency Declaration

If your package requires another Raiku package to be installed first, list it in `raiku.toml`:

```toml
dependencies = ["fast-math", "other-pkg"]
```

The CLI automatically resolves and installs dependencies in the correct order before the main package. Circular dependencies are detected and rejected.

---

## Tags

Tags help users discover packages via `raiku search --tag <tag>`. Add relevant tags in `raiku.toml`:

```toml
tags = ["math", "vectors", "linear-algebra"]
```

Use lowercase, hyphenated tags. Common categories: `math`, `utils`, `strings`, `collections`, `networking`, `concurrency`, `data-structures`, `geometry`, `io`, `parsing`, `testing`, `crypto`.

---

## CI Checks

Every PR automatically runs:

1. `raiku validate --all --strict` — all packages in the repository must pass
2. JSON lint on `index/index.json`
3. Schema check — every index entry must match `schemas/schema.yml`
4. Hash verification — `raiku index --check`
5. Full verification suite — `python _verify.py`

Your PR will not be merged until all CI checks pass.

---

## Review Process

- Maintainers review for correctness, safety, and rule compliance.
- Packages with dangerous build commands, suspicious code, or missing fields are rejected.
- Reviews typically complete within 3–5 business days.
- Once merged, the package is live immediately after the next `raiku sync`.

---

## Local Testing Before PR

```bash
# Full validation
raiku validate --dir UserSub/<Language>/my-package

# Install locally to test the build
raiku install ./UserSub/<Language>/my-package

# Run the full test suite
python _verify.py
python _smoke_new.py

# Rebuild index to confirm your entry is picked up
raiku index --rebuild --dry-run
```

---

## Getting Help

Open an issue at https://github.com/SGizek/Raiku/issues with label `question`.
