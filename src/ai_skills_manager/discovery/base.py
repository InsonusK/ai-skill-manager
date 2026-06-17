"""Base classes for skill discovery."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def is_skill_md(path: Path) -> bool:
    """Return True if path is a file matching *.skill.md."""
    return path.is_file() and path.name.endswith(".skill.md")


def skill_name_from_file(path: Path) -> str:
    """Extract skill name from a *.skill.md file name."""
    return path.name[:-9]  # strip '.skill.md'


@dataclass
class SkillMapping:
    """Maps a source to a target skill."""
    source_path: Path
    target_path: Path
    skill_name: str
    is_flat: bool
    source_skill_md: Optional[Path] = field(default=None)


class DiscoveryStrategy(ABC):
    """Abstract base for skill discovery strategies."""

    def __init__(self, source_path: Path, target_dir: Path):
        if not source_path.exists():
            logger.error("source_path not found: %s", source_path)
        self.source_path = source_path.resolve()
        self.target_dir = target_dir

    @abstractmethod
    def discover(self) -> List[SkillMapping]:
        """Discover skills and return list of mappings."""
        pass

    def _create_mapping(
        self,
        source: Path,
        name: str,
        is_flat: bool,
        source_skill_md: Optional[Path] = None,
    ) -> SkillMapping:
        """Helper to create a SkillMapping with resolved target path."""
        return SkillMapping(
            source_path=source,
            target_path=self.target_dir / name,
            skill_name=name,
            is_flat=is_flat,
            source_skill_md=source_skill_md,
        )
