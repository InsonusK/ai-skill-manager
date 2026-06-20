"""Base classes and helpers for link adapters."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .models.Link import Link
import yaml

from ai_skill_manager.models.skill import Skill

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SkillInfo:
    """Information about a skill extracted from its frontmatter."""

    name: str
    uid: str
    target_path: Path
    source_path: Path
    is_flat: bool


@dataclass
class FileContext:
    """Context for a single skill (source)."""

    skill: Optional[Skill]


@dataclass
class LinkContext(FileContext):
    """Context passed to link rules during adaptation.

    Inherits the skill from :class:`FileContext` and adds the concrete file
    being processed plus the registry mappings needed to resolve links.
    """

    filepath: Path
    file_skill: Optional[SkillInfo]
    repo_root: Path
    skills: Dict[str, SkillInfo]
    source_to_target: Dict[Path, Path]
    target_to_source: Dict[Path, Path]
    all_source_files: set[Path]
    target_to_skill: Dict[Path, SkillInfo]
    source_to_skill: Dict[Path, SkillInfo]


@dataclass
class AdaptResult:
    """Result of a successful link adaptation."""

    text: str
    status: str = "fixed"


@dataclass
class ReplaceResult:
    """Result of replacing links in a file."""

    new_path: Path
    fixes: list[dict]


def parse_skill_info(skill: Skill, target_name: Optional[str] = None) -> Optional[SkillInfo]:
    """Parse name and uid from a skill's SKILL.md frontmatter.

    Always returns a SkillInfo for valid skills, using fallback values
    when frontmatter is missing or incomplete.
    """
    skill_md = skill.file_path
    name = target_name if target_name is not None else skill.name
    if name is None:
        name = skill_md.name[:-9] if skill.is_flat() else skill_md.parent.name

    uid = None

    if skill_md.exists():
        try:
            content = skill_md.read_text(encoding="utf-8")
            if content.startswith("---"):
                end = content.find("\n---", 3)
                if end == -1:
                    end = content.find("\r\n---", 3)
                if end != -1:
                    frontmatter = yaml.safe_load(content[3:end])
                    if isinstance(frontmatter, dict):
                        uid = frontmatter.get("uid")
        except Exception as e:
            logger.warning("Failed to parse skill info from %s: %s", skill_md, e)

    if not uid:
        uid = f"auto-{hash(str(skill_md.resolve())) & 0xFFFFFFFF:08x}"
        logger.warning(
            "Skill %s at %s missing uid, using fallback %s",
            name, skill_md, uid
        )

    return SkillInfo(
        name=name,
        uid=uid,
        target_path=Path(".nonexistent"),  # set by caller
        source_path=skill.file_path,
        is_flat=skill.is_flat(),
    )


def resolve_target(path: Path, context: LinkContext) -> Optional[Path]:
    """Resolve a path to a managed target file.

    Tries the path as-is, with a ``.md`` extension, and as a directory
    containing ``SKILL.md``.
    """
    normalized = path.resolve()
    candidates = [normalized]
    if not normalized.suffix:
        candidates.append(Path(str(normalized) + ".md"))
    if not normalized.suffix or normalized.is_dir():
        candidates.append(normalized / "SKILL.md")

    for candidate in candidates:
        for src_file, target_file in context.source_to_target.items():
            if src_file.resolve() == candidate:
                return target_file
            if target_file.resolve() == candidate:
                return target_file
    return None


def format_link(link: Link, target_file: Path, context: LinkContext) -> str:
    """Format a link to a managed target file."""
    target_skill = context.target_to_skill.get(target_file)
    prefix = "!" if link.is_image else ""

    if target_skill and target_skill != context.file_skill and not link.is_image:
        url = f"skill: {target_skill.name}"
        if link.fragment:
            url += link.fragment
        return f"{prefix}[{link.text}]({url})"

    rel = os.path.relpath(target_file, context.filepath.parent).replace(os.sep, "/")
    return f"{prefix}[{link.text}]({rel}{link.fragment})"
