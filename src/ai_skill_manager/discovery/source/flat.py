"""Flat discovery strategy.

Treats *.skill.md files as individual flat skills.
"""

from pathlib import Path
from typing import List

from ...models.skill import Skill
from .base import DiscoveryStrategy, is_skill_md, skill_name_from_file


class FlatDiscovery(DiscoveryStrategy):
    """Treat *.skill.md files as flat skills."""

    def discover(self) -> List[Skill]:
        """Find *.skill.md files in source_path."""
        if not self.source_path.exists():
            return []

        if self.source_path.is_file():
            if is_skill_md(self.source_path):
                return [
                    self._create_skill(
                        file_path=self.source_path,
                    )
                ]
            return []

        results = []
        for skill_file in sorted(self.source_path.glob("*.skill.md")):
            results.append(
                self._create_skill(
                    file_path=skill_file,
                )
            )

        return results
