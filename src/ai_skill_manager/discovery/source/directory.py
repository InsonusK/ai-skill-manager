"""Directory discovery strategy.

Finds directories that contain a file named {directory_name}.skill.md.
"""

from pathlib import Path
from typing import List

from ...models.skill import Skill
from .base import DiscoveryStrategy
from ._common import discover_directory_skill


class DirectoryDiscovery(DiscoveryStrategy):
    """Find directory skills (subdirs with {dir_name}.skill.md)."""

    def discover(self) -> List[Skill]:
        """Find all directory skills under source_path."""
        if not self.source_path.exists():
            return []

        if self.source_path.is_file():
            return []

        # If source itself is a directory skill, return just it.
        skill_md = discover_directory_skill(self.source_path)
        if skill_md is not None:
            return [
                self._create_skill(
                    file_path=skill_md,
                    folder_path=self.source_path,
                )
            ]

        # Otherwise scan immediate subdirectories.
        results = []
        for subdir in sorted(self.source_path.iterdir()):
            if not subdir.is_dir():
                continue
            skill_md = discover_directory_skill(subdir)
            if skill_md is not None:
                results.append(
                    self._create_skill(
                        file_path=skill_md,
                        folder_path=subdir,
                    )
                )

        return results
