"""Base classes for skill discovery."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ...models.skill import Skill
from ...models.skill_format import SkillFormat

logger = logging.getLogger(__name__)


def is_skill_md(path: Path) -> bool:
    """Return True if path is a file matching *.skill.md."""
    return path.is_file() and path.name.endswith(".skill.md")


def skill_name_from_file(path: Path) -> str:
    """Extract skill name from a *.skill.md file name."""
    return path.name[:-9]  # strip '.skill.md'


class DiscoveryStrategy(ABC):
    """Abstract base for skill discovery strategies."""

    def __init__(self, source_path: Path):
        if not source_path.exists():
            logger.error("source_path not found: %s", source_path)
        self.source_path = source_path.resolve()

    @abstractmethod
    def discover(self) -> List[Skill]:
        """Discover skills and return list of Skill objects."""
        pass

    def _create_skill(
        self,
        file_path: Path,
        folder_path: Path | None = None,
        format: SkillFormat | None = None,
    ) -> Skill:
        """Helper to create a Skill from its markdown file and optional folder."""
        return Skill(
            file_path=file_path,
            folder_path=folder_path,
            format=format,
        )
