# Contributing to Raiku

Welcome. This guide explains how to add a package, update an existing one, and
what happens during review.

---

## Before You Start

1. Read [`rules.md`](../rules.md) — it is enforced strictly.
2. Install the Raiku CLI: `pip install -e .` from the repo root.
3. Make sure `raiku validate` and `raiku publish` are working: `raiku --version`.

---

## Adding a New Package

### Step 1 — Create the package directory

```
UserSub/<Language>/<your-package-name>/
  raiku.toml
  version.yml
  README.md
  src/
    <your source files>
```

Replace `<Language>` with one of: `Python`, `Rust`, `C`, `CPP`, `Zig`, `Java`, `CSharp`, `Go`.

### Step 2 — Write raiku.toml

```toml
name = "your-package-name"
version = "1.0.0"
language = "Python"          # exact, case-sensitive
author = "Your Name"
description = "One sentence about what this does."
license = "MIT"
build_command = "pip install -e ."
dependencies = []
```

### Step 3 — Write version.yml

```yaml
version: "1.0.0"          # must match raiku.toml exactly
release_date: "2026-07-03"
stability_level: stable
changelog:
  - "Initial release"
```

### Step 4 — Write README.md

Your README must contain at minimum:
- What the package does (1–2 sentences)
- How to install it (`raiku install <name>`)
- A basic usage example

### Step 5 — Validate

```bash
raiku validate --dir UserSub/<Language>/your-package-name
```

All checks must show `PASSED` with zero errors.

### Step 6 — Prepare the index entry

```bash
raiku publish --dir UserSub/<Language>/your-package-name
```

Copy the JSON block from the output and add it to `index/index.json` inside the
`"packages"` array.

### Step 7 — Open a Pull Request

Fork the repo, push your branch, open a PR:

- **Title**: `add(<Language>): your-package-name v1.0.0`
- **Body**: include the `raiku validate` output and a description of the package

---

## Updating an Existing Package

1. Bump `version` in both `raiku.toml` and `version.yml` (must match, must be higher).
2. Add an entry to `changelog` in `version.yml` describing what changed.
3. Update the `version` and `sha256` for your package in `index/index.json`
   (get the new sha256 from `raiku publish`).
4. Open a PR with title: `update(<Language>): package-name v<new-version>`

---

## CI Checks

Every PR runs the following automatically:

1. `raiku validate --all --strict` — all packages in the repo must pass
2. JSON lint on `index/index.json`
3. Schema check: every index entry must match `schemas/schema.yml`

Your PR will not be merged until all CI checks pass.

---

## Review Process

- Maintainers review for correctness, safety, and rule compliance.
- Packages with security concerns (dangerous build commands, suspicious code) are rejected.
- Reviews typically complete within 3–5 business days.
- Once approved and merged, the package appears in search results immediately after
  the next `raiku sync`.

---

## Getting Help

Open an issue at https://github.com/SGizek/Raiku/issues with label `question`.
