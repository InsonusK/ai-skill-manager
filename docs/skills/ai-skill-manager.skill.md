---
name: ai-skill-manager
description: Use the ai-skill-manager CLI to sync and validate AI agent skills from local directories or GitHub repositories into a target skills folder.
whenToUse: >
  Apply this skill when you need to install, import, or invoke ai-skill-manager
  to sync AI skills into `.agents/skills/`, `.claude/skills/`, or another target
  directory from a config file (`ai-skills.yaml`), a local path, or a GitHub
  repository.
tags:
  - ai-skill-manager
  - cli
  - skills
  - sync
  - validation
---

# Goal
- Give an AI agent exact commands to run `ai-skill-manager` for syncing and checking skills.
- Define the CLI entry points, required and optional arguments, config-file shape, and exit behavior.
- Make it possible to use the tool without reading human-oriented documentation.

# Core Principle
- Prefer `ai-skills.yaml` as the source of truth; use CLI flags only to override config values or for one-off checks.
- Always run `ai-skill-manager sync --dry-run` before writing changes when you are unsure what will be copied or deleted.
- Treat exit code `0` as success and `1` as failure; inspect the printed validation report or logs on failure.

# Rule

## MUST
- Install `ai-skill-manager` before first use:
  ```bash
  pip install git+https://github.com/InsonusK/ai-skill-manager.git
  ```
- Use one of the two entry points:
  ```bash
  ai-skill-manager <command> [options]
  aism <command> [options]
  ```
- Provide either a config file (`-c` or default `ai-skills.yaml`) **or** both `--type` and `--path` for source-less mode.
- Validate skills before syncing when the source is new or changed:
  ```bash
  ai-skill-manager check
  ```
- Use `--dry-run` to preview changes before applying them:
  ```bash
  ai-skill-manager sync --dry-run
  ```
- Resolve relative `settings.target` paths from the config file's directory.

## SHOULD
- Keep the default config file name `ai-skills.yaml` in the project root.
- Use `type: auto` for local directories unless you specifically need GitHub.
- Enable `--debug` when a command fails and the cause is unclear.

## MAY
- Use multi-target `settings.target` to write the same skills to both `.agents/skills` and `.claude/skills` with different adapters.
- Use `--profile` and `--profile-output <file>` to diagnose slow sync/check operations.

## SHOULD NOT
- Use `--force` routinely; it skips hash and version checks and may cause unnecessary writes.
- Pass `--remove-orphans` and `--keep-orphans` at the same time; they are mutually exclusive.

## MUST NOT
- Run `ai-skill-manager sync` against a target directory that contains hand-edited skills you do not want overwritten or removed.
- Point a GitHub source to a non-GitHub URL; the tool expects GitHub repository URLs.

# Reference

## Installation / access
```bash
pip install git+https://github.com/InsonusK/ai-skill-manager.git
```

After installation the console scripts `ai-skill-manager` and `aism` are available.

## Entry points
- `ai-skill-manager.cli:main` (Python module path used by `pyproject.toml`).
- Console scripts: `ai-skill-manager`, `aism`.

## Commands

### `sync`
Synchronizes discovered skills into the configured target directory(s).

**Usage**
```bash
ai-skill-manager sync [-c CONFIG] [-t {auto,github}] [-p PATH] [--subpath SUBPATH]
                      [--target TARGET] [--remove-orphans | --keep-orphans]
                      [--dry-run] [-f]
```

**Options**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-c`, `--config` | string | `ai-skills.yaml` | Path to the config file. |
| `-t`, `--type` | `auto` \| `github` | — | Source type for a single source. Requires `--path`. |
| `-p`, `--path` | string | — | Local source path or GitHub repo URL. Optional branch for GitHub: `"url branch"`. |
| `--subpath` | string (repeatable) | `skills` | Subpath(s) inside a GitHub repo to scan. |
| `--target` | string | from config | Override the target directory; replaces multi-target config with a single target. |
| `--remove-orphans` | flag | from config | Delete skills in target that are no longer in config. |
| `--keep-orphans` | flag | from config | Keep orphan skills in the target. |
| `--dry-run` | flag | `false` | Preview changes without writing files. |
| `-f`, `--force` | flag | `false` | Skip hash/version checks and copy all skills. |
| `--debug` | flag | `false` | Enable debug logging. |

**Output / return value**
- Prints a table of discovered skills and a summary of copied/skipped/removed counts.
- Returns exit code `0` on success, `1` on validation or runtime errors.

**Examples**
```bash
# Sync from default config
ai-skill-manager sync

# Preview changes
ai-skill-manager sync --dry-run

# Sync from a custom config
ai-skill-manager sync -c ./config/my-skills.yaml

# Sync a single GitHub source without a config file
ai-skill-manager sync -t github \
  -p "https://github.com/InsonusK/ai-skills.git main" \
  --subpath skills

# Force full re-copy
ai-skill-manager sync -f
```

### `check`
Discovers and validates skills without copying anything.

**Usage**
```bash
ai-skill-manager check [-c CONFIG] [-t {auto,github}] [-p PATH] [--subpath SUBPATH]
```

**Options**
- Same source-related options as `sync` (`-c`, `-t`, `-p`, `--subpath`) plus `--debug`.

**Output / return value**
- Prints the discovered skills and `✅ Validation passed` if no errors.
- Prints a validation report and returns `1` if validation fails.

**Examples**
```bash
# Check default config
ai-skill-manager check

# Check a local source
ai-skill-manager check -t auto -p ./my-skills

# Check a GitHub repo subpath
ai-skill-manager check -t github \
  -p "https://github.com/InsonusK/ai-skills.git main" \
  --subpath skills
```

### Global options
| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging. |
| `--profile` | Enable execution profiling and print top calls. |
| `--profile-output <file>` | Save raw profiling data (default: `ai-skill-manager.prof`). |

Profiling can also be enabled with `AI_SKILL_MANAGER_PROFILE=1`.

## Config file (`ai-skills.yaml`)

**Format**: YAML or JSON.

**Top-level keys**
```yaml
sources:
  - path: ./my-skills
    type: auto

settings:
  target: .agents/skills
  remove_orphans: true
  on_conflict: error
  dry_run: false
```

### `sources`
Each source is a mapping:

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `path` | yes | — | Local directory (relative to config) or GitHub repo URL. |
| `type` | no | `auto` | `auto` (local filesystem) or `github`. Legacy `flat`/`directory` are treated as `auto`. |
| `name` | no | — | Explicit skill name override. |

GitHub-only fields:

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `tree` | no | `master` | Branch or tag to download. |
| `subpath` | no | `skills` | Path or list of paths inside the repo to scan. |

### `settings`

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `target` | string or mapping | `.agents/skills` | Target directory or named multi-target mapping. |
| `remove_orphans` | boolean | `true` | Remove skills not present in config. |
| `on_conflict` | string | `error` | Duplicate skill name handling: `error` or `last_wins`. |
| `dry_run` | boolean | `false` | Preview changes without writing. |

### Multi-target example
```yaml
settings:
  target:
    for_each:
      adapters:
        - link-adapter
    default:
      path: .agents/skills
    claude:
      path: .claude/skills
      adapters:
        - claude-property-adapter
```

Reserved target names with default paths:
- `default` → `.agents/skills`
- `claude` → `.claude/skills`

Other target names require an explicit `path`.

### Available adapters
| Adapter | Description |
|---------|-------------|
| `link-adapter` | Rewrites internal skill links to repo-absolute targets. Used by default. |
| `claude-property-adapter` | Reshapes frontmatter to Claude Code native fields. |

## Source resolution order
1. Explicit `--config` path.
2. Direct source mode: `--type` + `--path`.
3. Default config file `ai-skills.yaml` in the current directory.

If none of these resolve, the command exits with code `1` and a `FileNotFoundError` message.

## Error handling / common failures
- `FileNotFoundError`: config file or source path does not exist. Verify the path and current working directory.
- `ValueError`: `--type` given without `--path`, unknown source type, or malformed `settings.target`. Provide both `--type` and `--path` or fix the config.
- `ValidationFailedError`: discovered skills are invalid. Read the printed validation report, fix the skill files, and rerun `check`.
- `--remove-orphans` + `--keep-orphans`: the last flag wins; avoid combining them.
- GitHub source fails to download: check the URL, branch name, and network access.

## Exit codes
| Code | Meaning |
|------|---------|
| `0` | Success (sync completed or validation passed). |
| `1` | Failure (file not found, validation error, unhandled exception). |

# Anti-patterns
- **Writing skills to the target directory by hand and then running `sync` with `remove_orphans: true`**
  - Consequence: hand-written skills that are not listed in `sources` are deleted.
  - Instead: add the source to `ai-skills.yaml` or set `remove_orphans: false` / pass `--keep-orphans`.

- **Using `--force` for every sync**
  - Consequence: hash and version checks are skipped, causing unnecessary writes and loss of incremental sync benefits.
  - Instead: use `--force` only after changing skill metadata or when the tool reports stale files.

- **Calling `ai-skill-manager sync` without `--dry-run` on a new config**
  - Consequence: unexpected files are copied or removed before you can review the plan.
  - Instead: run `ai-skill-manager sync --dry-run` first, then remove `--dry-run`.

- **Putting GitHub branches or tags in `path` instead of `tree`**
  - Consequence: the URL is malformed and the archive download fails.
  - Instead: use `path: https://github.com/owner/repo.git` and `tree: main`.

- **Relying on `docs/run.md` or `docs/config.md` instead of this skill**
  - Consequence: extra context-window usage and possible drift from the current CLI behavior.
  - Instead: use the commands and options listed here; refer to <https://github.com/InsonusK/ai-skill-manager/tree/master/docs/run.md> / <https://github.com/InsonusK/ai-skill-manager/tree/master/docs/config.md> only for deeper human-oriented background.

# Check list
- [ ] `ai-skill-manager` is installed and on `PATH`.
- [ ] The command uses the correct entry point (`ai-skill-manager` or `aism`).
- [ ] A config file or `--type` + `--path` is provided.
- [ ] `--dry-run` is used first when the outcome is uncertain.
- [ ] Mutually exclusive flags (`--remove-orphans` / `--keep-orphans`) are not combined.
- [ ] Exit code `1` is treated as failure and the printed error/validation report is read.
- [ ] Examples use exact commands, not conceptual descriptions.
