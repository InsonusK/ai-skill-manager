# Test Trace Matrix

Purpose: answer "what is covered by tests, and what is not" at a glance, without reading code.
See [no-test-theater](../../../../../.agents/skills/no-test-theater/SKILL.md).

## Module: `entities/source` — git-based repository fetch (private repo support)

Legend: Type `happy` | `boundary` | `negative` | `error` | `concurrency` | `security` | `regression";
Status ✅ covered | ⚠️ weak | ❌ not covered | 🔧 planned

| # | Scenario (Given-When-Then) | Type | Test(s) | Assert checks | Status |
|---|----------------------------|------|---------|---------------|--------|
| 1 | Given a reachable git repository, When cloning it without a tree override, Then the destination contains the repository files | happy | — | — | 🔧 |
| 2 | Given a repository with a non-default branch, When cloning with tree=<branch>, Then the destination contains that branch's files | happy | — | — | 🔧 |
| 3 | Given git executable is not in PATH, When cloning, Then GitCloneError is raised | error | — | — | 🔧 |
| 4 | Given an unreachable/invalid repository URL, When cloning, Then GitCloneError is raised with git's stderr | error | — | — | 🔧 |
| 5 | Given git is available, When fetch_repo_tree materializes a repo, Then git clone is used and the repo root is returned | happy | — | — | 🔧 |
| 6 | Given git is NOT available, When fetch_repo_tree materializes a GitHub repo, Then it falls back to the archive download and returns the extracted root | boundary | — | — | 🔧 |
| 7 | Given git is available but clone fails, When fetch_repo_tree materializes a GitHub repo, Then it falls back to the archive download | error | — | — | 🔧 |
| 8 | Given clone fails and the URL is not a GitHub URL, When fetch_repo_tree runs, Then the original GitCloneError is re-raised (no archive fallback possible) | negative | — | — | 🔧 |
| 9 | Given clone fails and the archive download also fails, When fetch_repo_tree runs, Then the archive download error propagates | error | — | — | 🔧 |
| 10 | Given a GitHubSource pointing at a local git repository (file path URL), When get_scan_locations runs, Then scan locations point into the cloned repository content | happy | — | — | 🔧 |

## Module summary

| Type | Total scenarios | ✅ Covered | ⚠️ Weak | ❌ Not covered |
|------|-----------------|-----------|---------|---------------|
| happy | 4 | 0 | 0 | 0 |
| boundary | 1 | 0 | 0 | 0 |
| negative | 1 | 0 | 0 | 0 |
| error | 4 | 0 | 0 | 0 |

## Function → Test (reverse breakdown)

Filled after tests are written.

| Public method / logic branch | Covering test(s) | Comment |
|------------------------------|------------------|---------|
| — | — | 🔧 pending |
