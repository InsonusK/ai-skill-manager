---
feature: sync-pipeline
depends_on:
  - src/ai_skill_manager/command/sync_command.py
  - src/ai_skill_manager/command/sync.py
  - src/ai_skill_manager/functions/skill_discovery.py
  - src/ai_skill_manager/functions/skill_dict_builder.py
  - src/ai_skill_manager/functions/file_discovery.py
  - src/ai_skill_manager/functions/link_discovery.py
  - src/ai_skill_manager/functions/skill_relation_queuer.py
  - src/ai_skill_manager/functions/skill_hash.py
  - src/ai_skill_manager/functions/skill_file_copier.py
  - src/ai_skill_manager/functions/external_file_copier.py
  - src/ai_skill_manager/functions/copied_link_rewriter.py
  - src/ai_skill_manager/functions/copy_skills/abs_copy_skills.py
  - src/ai_skill_manager/functions/copy_skills/default_copy_skills.py
  - src/ai_skill_manager/functions/copy_skills/claude_property_copy_skills.py
  - src/ai_skill_manager/functions/copy_skills/incremental_copy_skills.py
  - src/ai_skill_manager/functions/copy_skills/orphan_removing_copy_skills.py
  - src/ai_skill_manager/entities/skill_v2.py
  - src/ai_skill_manager/entities/skill_file_v2.py
  - src/ai_skill_manager/entities/skill_name.py
  - src/ai_skill_manager/entities/skill_kind.py
  - src/ai_skill_manager/entities/skill_at_path_finder.py
  - src/ai_skill_manager/service/discovery/discover.py
  - src/ai_skill_manager/service/discovery/skill/auto.py
  - src/ai_skill_manager/entities/link/link_target.py
  - src/ai_skill_manager/entities/link/link_target_resolver.py
  - src/ai_skill_manager/entities/link/file_link.py
  - src/ai_skill_manager/entities/link/file_link_factory.py
  - src/ai_skill_manager/entities/link/raw_path_resolution.py
---

# Sync pipeline

Discovers skills from configured sources, enriches them with files and
resolved links (queuing newly-discovered related skills for the same pass),
stops on any collected error, and otherwise copies skills into each
configured target — optionally skipping unchanged skills (incremental
hash-skip) and removing skills no longer present (orphan removal).

Replaces the former `discovery/` + `adapters/` + `validators/` split, where
the validator and the link-rewriting adapter each re-derived link targets
with divergent logic. Link targets are now resolved exactly once, at
discovery time, against the in-memory source skill graph — copying only
replays the already-resolved target, it never re-resolves.

## Capabilities

| capability | unit | kind |
| ---------- | ---- | ---- |
| Orchestrate discover → enrich → copy for one sync run | SyncCommand | Command |
| Build config-driven inputs and decorator chain for a sync run | run_sync | Command |
| Discover skills from configured sources | SkillDiscovery | Function |
| Merge discovered skills into the working dict, rejecting duplicate names | SkillDictBuilder | Function |
| Populate a skill's own file list, recursing into directory skills | FileDiscovery | Function |
| Find and resolve every link in a markdown file | LinkDiscovery | Function |
| Decide whether an unknown skill gets queued or reported as an error | SkillRelationQueuer | Function |
| Resolve a link's raw path to a `SkillLinkTarget`/`ExternalLinkTarget` | LinkTargetResolver | Function |
| Build one `FileLink` (raw text → target) for a raw link occurrence | FileLinkFactory | Function |
| Compute a content hash for a skill (for incremental skip) | compute_skill_hash | Function |
| Copy one skill's files into a target directory | SkillFileCopier | Function |
| Copy one file outside any skill into the target's shared files folder | ExternalFileCopier | Function |
| Rewrite a copied skill's links to point at copied destinations | CopiedLinkRewriter | Function |
| Copy skills as-is (base case) | DefaultCopySkills | Function |
| Reshape frontmatter for Claude-style targets while copying | ClaudePropertyCopySkills | Function |
| Skip re-copying a skill whose hash/version hasn't changed | IncrementalCopySkills | Function |
| Remove previously-managed skills no longer present in the source | OrphanRemovingCopySkills | Function |
| Validate/represent a skill's identity, kind and kebab-case name | Skill | Class |
| Represent one file (optionally markdown, with links) owned by a skill | SkillFile / MarkdownSkillFile | Class |
| Find a already-loaded-or-discoverable skill that owns a given path | SkillAtPathFinder | Function |

## Units

- **SyncCommand** (Command) — orchestrate discover → enrich (queue-driven, error-collecting) → copy for one sync run, with no business rules of its own beyond sequencing. This is also the seam between `FileDiscovery` and `LinkDiscovery`: it walks each skill's freshly-discovered files and calls `LinkDiscovery` on the markdown ones, so neither of those two units depends on the other.
  - depends on: skill discovery, skill dict building, file discovery, link discovery, a `CopySkills` per target
  - usage scenario: called once per sync invocation by `run_sync` with the resolved sources/targets; returns a `SyncResult` that either lists collected errors (nothing copied) or the synced skills.
  - test cases: [tests/command/test_sync_command.py](../../tests/command/test_sync_command.py), [tests/test_sync_command.py](../../tests/test_sync_command.py)

- **run_sync** (Command) — resolve config/CLI inputs into sources, targets and a `CopySkills` decorator chain, then delegate to `SyncCommand`.
  - depends on: config loader, `CopySkills` resolver, `SyncCommand`
  - usage scenario: called by `cli/sync.py` with typed parameters derived from argparse; returns the result dict the CLI formats, or raises `SyncFailedError` with the target left untouched.
  - test cases: [tests/test_sync_command.py](../../tests/test_sync_command.py), [tests/commands/test_sync_cli.py](../../tests/commands/test_sync_cli.py)

- **SkillDiscovery** (Function) — discover skills from a list of configured sources.
  - depends on: `service.discovery.discover` (pattern-matching scan + tag filtering, builds `Skill` directly)
  - usage scenario: called once at the start of a sync run with the resolved `Source` list; returns the discovered skills plus any per-candidate errors (e.g. a missing frontmatter name) - structural conflicts (ambiguous pattern matches) still raise.
  - test cases: [tests/functions/test_skill_discovery.py](../../tests/functions/test_skill_discovery.py), [tests/service/discovery/skill/test_auto.py](../../tests/service/discovery/skill/test_auto.py)

- **SkillDictBuilder** (Function) — merge a batch of skills into the working `name -> Skill` dict, reporting a duplicate name as an error instead of silently overwriting.
  - depends on: nothing beyond the `Skill` entities passed in
  - usage scenario: called with the initial discovery batch, then again with each newly-queued batch as `add_relations` grows the queue.
  - test cases: [tests/functions/test_skill_dict_builder.py](../../tests/functions/test_skill_dict_builder.py)

- **FileDiscovery** (Function) — populate one skill's `files` list: its own file, and every file under a directory skill. Only finds and classifies files - it does not know `LinkDiscovery` exists.
  - depends on: nothing beyond the `Skill` passed in
  - usage scenario: called once per skill in `SyncCommand`'s queue loop; mutates `skill.files` in place.
  - test cases: [tests/functions/test_file_discovery.py](../../tests/functions/test_file_discovery.py)

- **LinkDiscovery** (Function) — find every link in one markdown file's content, drop excluded links (inline code, web links, skip-folders), and resolve each remaining link's target via `FileLinkFactory`. Only resolves links for a file it's handed - it does not know `FileDiscovery` exists.
  - depends on: `discovery.link.search_links_in_content` (regex-based markdown/wiki parser, content-only), link exclude rules, `FileLinkFactory`
  - usage scenario: called once per markdown file by `SyncCommand`, after `FileDiscovery` has populated `skill.files`; returns the resolved `FileLink` list plus errors for links that could not be resolved.
  - test cases: [tests/functions/test_link_discovery.py](../../tests/functions/test_link_discovery.py)

- **SkillRelationQueuer** (Function) — decide whether a skill found at an unknown path gets appended to the discovery queue (`add_relations=True`) or reported as an "unknown file" error (`add_relations=False`), rejecting a name already queued.
  - depends on: nothing beyond the candidate `Skill` and the queue passed in
  - usage scenario: called by `FileLinkFactory`/`LinkTargetResolver` whenever a link resolves to a skill not yet in `known_skills`.
  - test cases: [tests/functions/test_skill_relation_queuer.py](../../tests/functions/test_skill_relation_queuer.py)

- **LinkTargetResolver** (Function) — resolve an OS-absolute path to a `SkillLinkTarget` (skill name + path relative to that skill) when the path belongs to a known skill.
  - depends on: nothing beyond the `known_skills` dict passed in
  - usage scenario: called by `FileLinkFactory` after classifying a raw link's absolute path.
  - test cases: [tests/entities/link/test_link_target_resolver.py](../../tests/entities/link/test_link_target_resolver.py)

- **FileLinkFactory** (Function) — build one `FileLink` from a raw link occurrence: resolve its raw path, determine skill vs. external target, and queue/report unknown skills via `SkillRelationQueuer`.
  - depends on: `LinkTargetResolver`, `SkillAtPathFinder`, `SkillRelationQueuer`
  - usage scenario: called once per raw link found by `LinkDiscovery`; returns the built `FileLink` or `None` plus an error message.
  - test cases: [tests/entities/link/test_file_link_factory.py](../../tests/entities/link/test_file_link_factory.py)

- **compute_skill_hash** (Function) — compute a content hash for a skill's files, used to detect "unchanged since last sync".
  - depends on: nothing beyond the `Skill` passed in
  - usage scenario: called by `IncrementalCopySkills` before copying, and after copying to persist the new hash in the managed-state marker.
  - test cases: [tests/functions/test_skill_hash.py](../../tests/functions/test_skill_hash.py)

- **SkillFileCopier** (Function) — copy one skill's own files into its destination folder under a target directory.
  - depends on: nothing beyond filesystem access
  - usage scenario: called by `DefaultCopySkills` for each skill being materialized.
  - test cases: [tests/functions/test_skill_file_copier.py](../../tests/functions/test_skill_file_copier.py)

- **ExternalFileCopier** (Function) — copy a file that does not belong to any skill into the target's shared files folder, deduplicating and renaming on collision.
  - depends on: nothing beyond filesystem access
  - usage scenario: called by `CopiedLinkRewriter` when a link's target is an `ExternalLinkTarget`.
  - test cases: [tests/functions/test_external_file_copier.py](../../tests/functions/test_external_file_copier.py)

- **CopiedLinkRewriter** (Function) — rewrite a copied skill's links to point at their copied destinations (skill-to-skill or skill-to-external-file), replacing unresolvable links with a placeholder instead of failing the whole copy.
  - depends on: `ExternalFileCopier`, the set of already-copied skill directories
  - usage scenario: called once per skill after all skills in a target have been physically copied, so cross-skill link targets are guaranteed to exist.
  - test cases: [tests/functions/test_copied_link_rewriter.py](../../tests/functions/test_copied_link_rewriter.py)

- **DefaultCopySkills** (Function) — copy every given skill's files then rewrite their links; the base `CopySkills` implementation other adapters wrap.
  - depends on: `SkillFileCopier`, `CopiedLinkRewriter`
  - usage scenario: used directly for targets with no special output shape (e.g. `.agents/skills`); wrapped by the other `CopySkills` decorators for targets that need more.
  - test cases: [tests/functions/test_copy_skills.py](../../tests/functions/test_copy_skills.py)

- **ClaudePropertyCopySkills** (Function) — after the wrapped copy, reshape each copied skill's frontmatter into Claude's native property set.
  - depends on: a wrapped `CopySkills`
  - usage scenario: configured for targets like `.claude/skills` via `settings.target.<name>.adapters: [claude-property-adapter]`.
  - test cases: [tests/functions/test_copy_skills.py](../../tests/functions/test_copy_skills.py)

- **IncrementalCopySkills** (Function) — skip copying a skill whose hash and adapter version already match the managed-state marker from a previous sync; always includes skipped skills in `skills` for cross-reference resolution via `skip_names`.
  - depends on: a wrapped `CopySkills`, `compute_skill_hash`, the managed-state marker
  - usage scenario: applied to every target's `CopySkills` chain by `run_sync` unless `--force` is passed.
  - test cases: [tests/functions/test_incremental_copy_skills.py](../../tests/functions/test_incremental_copy_skills.py)

- **OrphanRemovingCopySkills** (Function) — after the wrapped copy, remove previously-managed skill folders in the target that are no longer present in the source.
  - depends on: a wrapped `CopySkills`, the managed-state marker
  - usage scenario: applied to every target's `CopySkills` chain by `run_sync` unless `remove_orphans=False`.
  - test cases: [tests/functions/test_orphan_removing_copy_skills.py](../../tests/functions/test_orphan_removing_copy_skills.py)

- **Skill** (Class) — identity and structure of one discovered skill: name (validated kebab-case), path, kind, main file, and enriched file list. Also resolves one of its own files' repo-absolute path (`file_absolute_path`), used by `SyncCommand` to hand `LinkDiscovery` the right file.
  - depends on: `is_kebab_case`
  - usage scenario: built directly by the `AutoDiscovery` pattern templates (reading the name from frontmatter) at discovery time, then mutated in place by `FileDiscovery` (files) and `LinkDiscovery` (links), both called from `SyncCommand`.
  - test cases: [tests/entities/test_skill_v2.py](../../tests/entities/test_skill_v2.py), [tests/entities/test_kebab_case_name.py](../../tests/entities/test_kebab_case_name.py), [tests/service/discovery/skill/test_auto.py](../../tests/service/discovery/skill/test_auto.py)

- **SkillFile / MarkdownSkillFile** (Class) — one file owned by a skill; the markdown subclass adds the file's resolved `links`.
  - depends on: nothing
  - usage scenario: constructed by `FileDiscovery` for every file under a skill, markdown files get the `MarkdownSkillFile` subclass so `LinkDiscovery` has somewhere to attach `FileLink`s.
  - test cases: [tests/entities/test_skill_file_v2.py](../../tests/entities/test_skill_file_v2.py)

- **SkillAtPathFinder** (Function) — find a skill (already loaded or freshly discoverable) that owns a given filesystem path.
  - depends on: `AutoDiscovery` (scoped to a candidate path)
  - usage scenario: called by `FileLinkFactory` when a link's resolved path isn't under the source repo path but might still belong to a not-yet-loaded skill.
  - test cases: [tests/entities/test_skill_at_path_finder.py](../../tests/entities/test_skill_at_path_finder.py)

## Diagram

Not rendered: this environment has no `diagram-renderer` CLI installed (only
referenced by the `solid-decomposition` skill's own docs, not present as an
executable here). Per that skill's own rule, a diagram must not be hand-drawn
as a substitute — the `depends_on` links above are accurate and ready for
`diagram-renderer` to consume once it's available; the diagram itself is
absent rather than faked.
