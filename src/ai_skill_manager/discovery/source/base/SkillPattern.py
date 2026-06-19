from typing import Optional

from ....models import Skill,SkillFormat

from abc import ABC, abstractmethod
from pathlib import Path


class SkillPattern(ABC):
    """Internal pattern that can match a path to a skill."""

    @property
    @abstractmethod
    def skill_format(self) -> SkillFormat:
        """Format produced by this pattern."""
        ...

    @abstractmethod
    def match(self, path: Path) -> Optional[Skill]:
        """Return a :class:`Skill` if ``path`` matches this pattern."""
        ...