"""Core synchronization logic."""

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .adapters.link_updater import LinkUpdater
from .config import load_config
from .discovery import Source, discover
from .models.skill import Skill
from .utils import compute_hash, is_managed, read_managed_state, tag_managed, write_managed_state


@dataclass
class _SyncSkill:
    """Internal wrapper pairing a discovered Skill with its target name."""

    skill: Skill
    target_name: str


def build_source_to_target_map(
    sync_skills: List[_SyncSkill], target_dir: Path
) -> Dict[Path, Path]:
    """Build map from source file path to target file path."""
    result = {}
    for sync_skill in sync_skills:
        skill = sync_skill.skill
        skill_target_dir = target_dir / sync_skill.target_name
        if skill.is_flat():
            result[skill.file_path] = skill_target_dir / "SKILL.md"
        else:
            source_dir = skill.folder_path
            skill_md = skill.file_path
            for src_file in source_dir.rglob("*"):
                if src_file.is_file():
                    rel = src_file.relative_to(source_dir)
                    if src_file == skill_md.resolve():
                        result[src_file] = skill_target_dir / "SKILL.md"
                    else:
                        result[src_file] = skill_target_dir / rel
    return result


def collect_source_files(sync_skills: List[_SyncSkill]) -> set:
    """Collect all source file paths."""
    files = set()
    for sync_skill in sync_skills:
        skill = sync_skill.skill
        if skill.is_flat():
            files.add(skill.file_path)
        else:
            files.update(skill.folder_path.rglob("*"))
    return {p for p in files if p.is_file()}


def compute_skill_hash(sync_skill: _SyncSkill) -> str:
    """Compute hash of a skill source."""
    skill = sync_skill.skill
    if skill.is_flat():
        return compute_hash(skill.file_path)
    h = hashlib.sha256()
    for file_path in sorted(skill.folder_path.rglob("*")):
        if file_path.is_file():
            rel = str(file_path.relative_to(skill.folder_path))
            h.update(rel.encode())
            h.update(compute_hash(file_path).encode())
    return h.hexdigest()


def _copy_directory_skill(sync_skill: _SyncSkill, target_dir: Path) -> None:
    """Copy a directory skill, renaming the source skill markdown to SKILL.md."""
    source_dir = sync_skill.skill.folder_path
    target_dir = target_dir / sync_skill.target_name
    skill_md = sync_skill.skill.file_path

    target_dir.mkdir(parents=True, exist_ok=True)
    for src_file in sorted(source_dir.rglob("*")):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(source_dir)
        if src_file == skill_md.resolve():
            dst = target_dir / "SKILL.md"
        else:
            dst = target_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst)


def copy_skill(
    sync_skill: _SyncSkill, target_dir: Path, dry_run: bool, adapters: Optional[List] = None
) -> None:
    """Copy a skill from source to target."""
    if dry_run:
        return

    skill_target_dir = target_dir / sync_skill.target_name
    if skill_target_dir.exists():
        shutil.rmtree(skill_target_dir)

    skill = sync_skill.skill
    if skill.is_flat():
        skill_target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill.file_path, skill_target_dir / "SKILL.md")
    else:
        _copy_directory_skill(sync_skill, target_dir)

    tag_managed(skill_target_dir)

    state = {
        "hash": compute_skill_hash(sync_skill),
        "adapters": [
            {"name": adapter.__class__.__name__, "version": getattr(adapter, "version", 1)}
            for adapter in (adapters or [])
        ],
    }
    write_managed_state(skill_target_dir, state)


def should_copy_skill(
    sync_skill: _SyncSkill, target_dir: Path, adapters: List, force: bool = False
) -> bool:
    """Check if skill needs to be copied based on hash and adapter versions."""
    if force:
        return True

    skill_target_dir = target_dir / sync_skill.target_name
    if not is_managed(skill_target_dir):
        return True

    state = read_managed_state(skill_target_dir)
    if state is None:
        return True

    current_hash = compute_skill_hash(sync_skill)
    if state.get("hash") != current_hash:
        return True

    current_adapters = sorted(
        [
            {"name": adapter.__class__.__name__, "version": getattr(adapter, "version", 1)}
            for adapter in adapters
        ],
        key=lambda x: x["name"],
    )
    previous_adapters = sorted(
        state.get("adapters", []),
        key=lambda x: x.get("name", ""),
    )
    if current_adapters != previous_adapters:
        return True

    return False


def remove_orphans(target_dir: Path, valid_names: set, dry_run: bool) -> None:
    """Remove skills not in the valid set."""
    if not target_dir.exists():
        return

    for item in target_dir.iterdir():
        if item.is_dir() and is_managed(item) and item.name not in valid_names:
            if not dry_run:
                shutil.rmtree(item)


class SkillSync:
    """Main synchronization orchestrator."""

    def __init__(
        self,
        config_file: Path,
        target_dir: Optional[Path] = None,
        on_conflict: str = "error",
        remove_orphans: bool = True,
        dry_run: bool = False,
        force: bool = False,
    ):
        self.config_file = Path(config_file).resolve()
        self.config_dir = self.config_file.parent
        self.target_dir = target_dir or (self.config_dir / ".agents" / "skills")
        self.on_conflict = on_conflict
        self.remove_orphans = remove_orphans
        self.dry_run = dry_run
        self.force = force
        self.skills: List[_SyncSkill] = []

    def _resolve_conflicts(self, sync_skills: List[_SyncSkill]) -> List[_SyncSkill]:
        """Handle skill name conflicts."""
        name_to_sync_skill: Dict[str, _SyncSkill] = {}

        for sync_skill in sync_skills:
            target_name = sync_skill.target_name
            if target_name in name_to_sync_skill:
                if self.on_conflict == "error":
                    existing = name_to_sync_skill[target_name].skill.file_path
                    raise ValueError(
                        f"CONFLICT: Skill '{target_name}' from {existing} "
                        f"and {sync_skill.skill.file_path}"
                    )
                # last_wins: overwrite

            name_to_sync_skill[target_name] = sync_skill

        return list(name_to_sync_skill.values())

    def sync(self) -> dict:
        """Run full synchronization."""
        config = load_config(self.config_file)
        settings = config.get("settings", {})
        sources = config.get("sources", [])

        # Override from config
        if "target" in settings and not self.target_dir:
            self.target_dir = self.config_dir / settings["target"]
        if "on_conflict" in settings:
            self.on_conflict = settings["on_conflict"]
        if "remove_orphans" in settings:
            self.remove_orphans = settings["remove_orphans"]
        if settings.get("dry_run", False):
            self.dry_run = True

        # Discover skills from all sources
        all_sync_skills: List[_SyncSkill] = []

        for src in sources:
            src_type = src.get("type", "auto")
            src_path = src.get("path", "")
            if src_type != "github":
                src_path = str(self.config_dir / src_path)

            source = Source(
                type=src_type,
                path=src_path,
                tree=src.get("tree", "master"),
                subpath=src.get("subpath"),
            )
            discovered = discover([source])

            override_name = src.get("name")
            for skill in discovered:
                target_name = override_name if override_name is not None else skill.name
                if target_name is None:
                    raise ValueError(
                        f"Skill {skill.file_path} has no 'name' in frontmatter and no override"
                    )
                all_sync_skills.append(_SyncSkill(skill=skill, target_name=target_name))

        # Resolve conflicts
        self.skills = self._resolve_conflicts(all_sync_skills)

        # Build maps
        source_to_target = build_source_to_target_map(self.skills, self.target_dir)
        all_source_files = collect_source_files(self.skills)

        # Prepare adapters
        target_names = {s.skill.file_path: s.target_name for s in self.skills}
        updater = LinkUpdater(
            [s.skill for s in self.skills],
            self.target_dir,
            source_to_target,
            all_source_files,
            target_names=target_names,
            dry_run=self.dry_run,
        )
        adapters = [updater]

        # Ensure target exists
        if not self.dry_run:
            self.target_dir.mkdir(parents=True, exist_ok=True)

        # Copy skills
        skipped = 0
        for sync_skill in self.skills:
            skill_target_dir = self.target_dir / sync_skill.target_name
            if skill_target_dir.exists() and not is_managed(skill_target_dir):
                continue  # Skip non-managed existing skills
            if not should_copy_skill(sync_skill, self.target_dir, adapters, force=self.force):
                skipped += 1
                continue
            copy_skill(sync_skill, self.target_dir, self.dry_run, adapters=adapters)

        # Fix links
        fixes = updater.adapt_all(self.target_dir)

        fix_summary = {}
        for fix in fixes:
            fix_summary[fix["status"]] = fix_summary.get(fix["status"], 0) + 1

        # Remove orphans
        if self.remove_orphans:
            valid_names = {s.target_name for s in self.skills}
            remove_orphans(self.target_dir, valid_names, self.dry_run)

        return {
            "synced_count": len(self.skills) - skipped,
            "skipped_count": skipped,
            "fix_summary": fix_summary,
            "fixes": fixes,
            "dry_run": self.dry_run,
        }
