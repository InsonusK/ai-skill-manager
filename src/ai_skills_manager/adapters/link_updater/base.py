"""Base classes and helpers for link adapters."""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Literal

import yaml

from ai_skills_manager.discovery.base import SkillMapping

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
class Link:
    """Represents a parsed link found in markdown content."""
    full_match: str
    link_type: Literal['markdown', 'wiki']
    text: str
    target: str
    fragment: str
    is_image: bool


@dataclass
class AdaptContext:
    """Context passed to link adapters during adaptation."""
    filepath: Path
    file_skill: Optional[SkillInfo]
    source_to_target: Dict[Path, Path]
    all_source_files: set[Path]
    target_to_skill: Dict[Path, SkillInfo]
    source_to_skill: Dict[Path, SkillInfo]
    mappings: Dict[str, SkillMapping]


@dataclass
class AdaptResult:
    """Result of a successful link adaptation."""
    text: str
    status: str = "fixed"


class LinkTypeAdapter(ABC):
    """Base class for concrete link type adapters."""

    @abstractmethod
    def is_match(self, link: Link) -> bool:
        """Check if this adapter can handle the given link.

        Returns True if the link belongs to this adapter's domain.
        """
        pass

    @abstractmethod
    def adapt(self, link: Link, context: AdaptContext) -> Optional[AdaptResult]:
        """Adapt the link to the target format.

        Returns AdaptResult on success, or None if the link is broken
        and should be left unchanged.
        """
        pass


def parse_skill_info(mapping: SkillMapping) -> Optional[SkillInfo]:
    """Parse name and uid from a skill's SKILL.md frontmatter.

    Always returns a SkillInfo for valid mappings, using fallback values
    when frontmatter is missing or incomplete.
    """
    if mapping.source_skill_md is not None:
        skill_md = mapping.source_skill_md
    elif mapping.is_flat:
        skill_md = mapping.source_path
    else:
        skill_md = mapping.source_path / 'SKILL.md'

    name = mapping.skill_name
    uid = None

    if skill_md.exists():
        try:
            content = skill_md.read_text(encoding='utf-8')
            if content.startswith('---'):
                end = content.find('\n---', 3)
                if end == -1:
                    end = content.find('\r\n---', 3)
                if end != -1:
                    frontmatter = yaml.safe_load(content[3:end])
                    if isinstance(frontmatter, dict):
                        name = frontmatter.get('name', name)
                        uid = frontmatter.get('uid')
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
        target_path=mapping.target_path,
        source_path=mapping.source_path,
        is_flat=mapping.is_flat,
    )


def find_source_dir_for_file(
    filepath: Path,
    file_skill: Optional[SkillInfo],
    mappings: Dict[str, SkillMapping],
) -> Optional[Path]:
    """Determine the source directory corresponding to a target file."""
    if not file_skill:
        return None

    mapping = mappings.get(file_skill.name)
    if not mapping:
        return None

    if mapping.is_flat:
        return mapping.source_path.parent
    else:
        try:
            rel = filepath.relative_to(mapping.target_path)
            return mapping.source_path / rel.parent
        except ValueError:
            return mapping.source_path


def format_managed_link(
    target_file: Path,
    text: str,
    fragment: str,
    is_image: bool,
    context: AdaptContext,
) -> Optional[AdaptResult]:
    """Format a link to a managed (known) target file."""
    target_skill = context.target_to_skill.get(target_file)
    prefix = "!" if is_image else ""

    if target_skill and target_skill != context.file_skill and not is_image:
        # Cross-skill link -> skill link format
        header = fragment.lstrip('#')
        if header:
            link_url = f"{target_skill.name}|uid: {target_skill.uid}|#{header}"
        else:
            link_url = f"{target_skill.name}|uid: {target_skill.uid}"
        return AdaptResult(
            text=f"{prefix}[{text}]({link_url})",
            status="fixed",
        )
    else:
        # Same skill or image -> relative path
        try:
            rel = os.path.relpath(target_file, context.filepath.parent).replace(os.sep, "/")
            return AdaptResult(
                text=f"{prefix}[{text}]({rel}{fragment})",
                status="fixed",
            )
        except ValueError:
            return None
