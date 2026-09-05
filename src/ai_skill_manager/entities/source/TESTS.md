# Test Trace Matrix

Purpose: answer "what is covered by tests, and what is not" at a glance, without reading code.
See [no-test-theater](../../../../../.agents/skills/no-test-theater/SKILL.md).

## Module: `entities/source` — git-based repository fetch (private repo support)

Legend: Type `happy` | `boundary` | `negative` | `error` | `concurrency` | `security` | `regression"
Status ✅ covered | ⚠️ weak | ❌ not covered | 🔧 planned

| # | Scenario (Given-When-Then) | Type | Test(s) | Assert checks | Status |
|---|----------------------------|------|---------|---------------|--------|
| 1 | Given a reachable git repository, When cloning it without a tree override, Then the destination contains the repository files | happy | `test_clone_copies_repository_files` | `dest/SKILL.md` content == "# Skill"; returned path == dest | ✅ |
| 2 | Given a repository with a non-default branch, When cloning with tree=<branch>, Then the destination contains that branch's files | happy | `test_clone_checks_out_requested_tree` | `dest/feature.txt` exists with content "feature" | ✅ |
| 3 | Given git executable is not in PATH, When cloning, Then GitCloneError is raised | error | `test_clone_raises_when_git_executable_missing` | `GitCloneError` raised, message mentions "git" (via `shutil.which` patched to None) | ✅ |
| 4 | Given an unreachable/invalid repository URL, When cloning, Then GitCloneError is raised with git's stderr | error | `test_clone_raises_with_stderr_when_clone_fails` | `GitCloneError` raised, message contains the failing URL | ✅ |
| 5 | Given git is available, When fetch_repo_tree materializes a repo, Then git clone is used and the repo root is returned | happy | `test_uses_git_clone_when_available` | returned root's `marker.txt` content == "cloned-content" (real local git repo, no mocks) | ✅ |
| 6 | Given git is NOT available, When fetch_repo_tree materializes a GitHub repo, Then it falls back to the archive download and returns the extracted root | boundary | `test_falls_back_to_archive_when_git_missing` | `_download_archive` called with ("owner", "repo", "main"); extracted `marker.txt` content == "archive-content" | ✅ |
| 7 | Given git is available but clone fails, When fetch_repo_tree materializes a GitHub repo, Then it falls back to the archive download | error | `test_falls_back_to_archive_when_clone_fails` | extracted `marker.txt` content == "archive-content" despite `GitCloneError` from clone | ✅ |
| 7a | Given a failed clone left a partial `repo/` directory, When falling back to the archive, Then the partial directory is removed before extraction | error | `test_removes_partial_clone_directory_before_archive_fallback` | returned root has `marker.txt`; `work_dir/repo` no longer exists | ✅ |
| 8 | Given clone fails and the URL is not a GitHub URL, When fetch_repo_tree runs, Then the original GitCloneError is re-raised (no archive fallback possible) | negative | `test_reraises_clone_error_when_url_is_not_github` | `GitCloneError` (not `ValueError`) raised with "denied" in message; `_download_archive` not called | ✅ |
| 9 | Given clone fails and the archive download also fails, When fetch_repo_tree runs, Then the archive download error propagates | error | `test_archive_error_propagates_when_both_strategies_fail` | `RuntimeError("archive download failed")` propagates | ✅ |
| 10 | Given a GitHubSource pointing at a local git repository (file path URL), When get_scan_locations runs, Then scan locations point into the cloned repository content | happy | `test_scan_locations_point_into_cloned_repository` | 1 location; `scan_path/marker.txt` content == "cloned-content"; `repo_path == scan_path` | ✅ |
| 11 | Given two GitHubSource instances with materialized repositories, When cleanup is called on the first, Then only its own repository is removed and the second's stays intact until its own cleanup | regression | `test_cleanup_of_one_source_leaves_other_sources_repository` | after `source_a.cleanup()`: `path_a` gone, `path_b` exists; after `source_b.cleanup()`: `path_b` gone | ✅ |

Note on mocks: rows 6-9 mock `clone_git_repo`/`_download_archive` at the `github` module boundary
to simulate git-missing/clone-failure without depending on machine git state; every mock has a
concrete assert on the resulting filesystem content or the exact exception, so the tests fail if
the fallback wiring breaks. Rows 1, 2, 5, 10 use real local git repositories and no mocks.

## Module summary

| Type | Total scenarios | ✅ Covered | ⚠️ Weak | ❌ Not covered |
|------|-----------------|-----------|---------|---------------|
| happy | 4 | 4 | 0 | 0 |
| boundary | 1 | 1 | 0 | 0 |
| negative | 1 | 1 | 0 | 0 |
| error | 5 | 5 | 0 | 0 |
| regression | 1 | 1 | 0 | 0 |

No ❌ rows — all happy/negative/error scenarios covered.

## Function → Test (reverse breakdown)

| Public method / logic branch | Covering test(s) | Comment |
|------------------------------|------------------|---------|
| `clone_git_repo()` — happy path | `test_clone_copies_repository_files`, `test_clone_checks_out_requested_tree` | real local repos |
| `clone_git_repo()` — git not in PATH branch | `test_clone_raises_when_git_executable_missing` | `shutil.which` patched |
| `clone_git_repo()` — non-zero exit branch | `test_clone_raises_with_stderr_when_clone_fails` | message includes URL |
| `fetch_repo_tree()` — clone success path | `test_uses_git_clone_when_available` | |
| `fetch_repo_tree()` — clone failure + GitHub URL → archive fallback | `test_falls_back_to_archive_when_git_missing` (covers both "git missing" and "clone raised"), `test_falls_back_to_archive_when_clone_fails` | |
| `fetch_repo_tree()` — partial clone dir cleanup branch | `test_removes_partial_clone_directory_before_archive_fallback` | side effect creates dir, then raises |
| `fetch_repo_tree()` — clone failure + non-GitHub URL → re-raise | `test_reraises_clone_error_when_url_is_not_github` | regression: `except ... as` variable is deleted after the block, so the error is bound to a separate variable |
| `fetch_repo_tree()` — both strategies fail | `test_archive_error_propagates_when_both_strategies_fail` | |
| `GitHubSource.get_scan_locations()` — git-clone materialization | `test_scan_locations_point_into_cloned_repository` | end-to-end through the entity |
| `GitHubSource.cleanup()` — removes only own extracted dirs (per-instance `Context`, not shared class attribute) | `test_cleanup_of_one_source_leaves_other_sources_repository` | regression: `Context.extracted_dirs` was a class-level list shared between instances |
