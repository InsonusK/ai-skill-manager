"""Updates links after skill sync.

Rules:
- Links within same skill -> relative Markdown path
- Links to other managed skills -> ``[text](skill: skill-name)``
- Links to external files -> forbidden (marked broken)
- Broken links -> left as-is, reported in validation

Supported link types:
- Markdown relative links: ``[text](./relative/path)`` and ``[text](../relative/path)``
- Wiki absolute links: ``[[absolute/path|text]]`` from the skills repo root
- Wiki relative links: ``[[./relative/path|text]]`` and ``[[../relative/path|text]]`` from the current file
- Plain wiki links by file name: ``[[file name|text]]`` -> forbidden

Context hierarchy:
- :class:`FileContext` carries the :class:`Skill` (and therefore its ``Source``).
- :class:`LinkContext` inherits from :class:`FileContext` and adds the concrete
  file being processed plus the registries needed to resolve links.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from .models.link_location import LinkLocation

from .models.link import Link
from ai_skill_manager.models.skill import Skill

from .service.LinkFactory import LinkFactory

from .base import (
    AdaptResult,
    FileContext,
    LinkContext,
    ReplaceResult,
    SkillInfo,
    parse_skill_info,
)
from .map import LinkMapError, LinkMapper
from .replace import LinkReplacer
from .rules import (
    LinkRule,
    MarkdawnLinkRule,
    MarkdawnRelativeRule,
    WikilinkAbsoluteRule,
    WikilinkRelativeRule,
    WikilinkRule,
)

logger = logging.getLogger(__name__)

__all__ = [
    "AdaptResult",
    "FileContext",
    "Link",
    "LinkContext",
    "LinkFactory",
    "LinkLocation",
    "LinkMapError",
    "LinkMapper",
    "LinkReplacer",
    "LinkRule",
    "LinkUpdater",
    "MarkdawnLinkRule",
    "MarkdawnRelativeRule",
    "WikilinkRule",
    "ReplaceResult",
    "SkillInfo",
    "WikilinkAbsoluteRule",
    "WikilinkRelativeRule",
    "parse_skill_info",
]


class LinkUpdater:
    """Main link updater that registers and orchestrates link replacement."""

    @property
    def version(self) -> int:
        return 3

    def __init__(
        self,
        skills: List[Skill],
        target_dir: Path,
        source_to_target: dict[Path, Path],
        all_source_files: set[Path],
        target_names: Optional[Dict[Path, str]] = None,
        dry_run: bool = False,
    ):
        self._skills = skills
        self.target_names = target_names or {}
        self.target_dir = target_dir
        self.source_to_target = source_to_target
        self.all_source_files = all_source_files
        self.dry_run = dry_run
        self.fixes: List[dict] = []
        self.replacer = LinkReplacer()

        # Build skill registries
        self.skill_infos: dict[str, SkillInfo] = {}
        self.source_to_skill: dict[Path, SkillInfo] = {}
        self.target_to_skill: dict[Path, SkillInfo] = {}
        self.target_to_source: dict[Path, Path] = {v: k for k, v in source_to_target.items()}
        self._skill_by_name: dict[str, Skill] = {}
        self._skill_by_source_path: dict[Path, Skill] = {}

        for skill in skills:
            target_name = self.target_names.get(skill.file_path, skill.name)
            self._skill_by_name[target_name] = skill
            self._skill_by_source_path[skill.file_path] = skill

        for skill in skills:
            target_name = self.target_names.get(skill.file_path, skill.name)
            skill_info = parse_skill_info(skill, target_name=target_name)
            if skill_info:
                self.skill_infos[target_name] = SkillInfo(
                    name=skill_info.name,
                    uid=skill_info.uid,
                    target_path=target_dir / target_name,
                    source_path=skill_info.source_path,
                    is_flat=skill_info.is_flat,
                )

        # Map each source file to its skill
        for src_file in all_source_files:
            for skill in skills:
                target_name = self.target_names.get(skill.file_path, skill.name)
                skill_info = self.skill_infos.get(target_name)
                if not skill_info:
                    continue
                if skill.is_flat():
                    if src_file == skill.file_path:
                        self.source_to_skill[src_file] = skill_info
                        break
                else:
                    try:
                        src_file.relative_to(skill.folder_path)
                        self.source_to_skill[src_file] = skill_info
                        break
                    except ValueError:
                        continue

        # Map each target file to its skill via source_to_target
        for src_file, target_file in source_to_target.items():
            skill_info = self.source_to_skill.get(src_file)
            if skill_info:
                self.target_to_skill[target_file] = skill_info

    def _find_skill_for_file(self, filepath: Path) -> Optional[SkillInfo]:
        """Find skill info for a target file."""
        skill_info = self.target_to_skill.get(filepath)
        if skill_info:
            return skill_info

        for skill in self._skills:
            target_name = self.target_names.get(skill.file_path, skill.name)
            skill_info = self.skill_infos.get(target_name)
            if not skill_info:
                continue
            if skill.is_flat():
                if filepath == self.target_dir / target_name / "SKILL.md":
                    return skill_info
            else:
                try:
                    filepath.relative_to(self.target_dir / target_name)
                    return skill_info
                except ValueError:
                    continue

        return None

    def _find_skill_object_for_file(self, filepath: Path) -> Optional[Skill]:
        """Find the original Skill object for a target file."""
        skill_info = self._find_skill_for_file(filepath)
        if skill_info:
            return self._skill_by_name.get(skill_info.name)

        # Fallback: infer from target path structure
        for skill in self._skills:
            target_name = self.target_names.get(skill.file_path, skill.name)
            skill_info = self.skill_infos.get(target_name)
            if not skill_info:
                continue
            if skill.is_flat():
                if filepath == self.target_dir / target_name / "SKILL.md":
                    return skill
            else:
                try:
                    filepath.relative_to(self.target_dir / target_name)
                    return skill
                except ValueError:
                    continue

        return None

    def _build_context(self, filepath: Path) -> LinkContext:
        """Build the adaptation context for a file."""
        return LinkContext(
            skill=self._find_skill_object_for_file(filepath),
            filepath=filepath,
            file_skill=self._find_skill_for_file(filepath),
            repo_root=self.target_dir,
            skills=self.skill_infos,
            source_to_target=self.source_to_target,
            target_to_source=self.target_to_source,
            all_source_files=self.all_source_files,
            target_to_skill=self.target_to_skill,
            source_to_skill=self.source_to_skill,
        )

    def adapt(self, filepath: Path) -> None:
        """Update links in a single markdown file."""
        if not filepath.exists() or filepath.suffix != ".md":
            return

        context = self._build_context(filepath)
        result = self.replacer.replace(context)

        if not self.dry_run:
            os.replace(str(result.new_path), str(filepath))
        else:
            result.new_path.unlink(missing_ok=True)

        self.fixes.extend(result.fixes)

    def adapt_all(self, target_dir: Path) -> List[dict]:
        """Update links in all markdown files under target_dir."""
        self.fixes = []
        if not target_dir.exists():
            return self.fixes

        for md_file in target_dir.rglob("*.md"):
            self.adapt(md_file)

        return self.fixes
