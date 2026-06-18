"""Directory discovery strategy.

Finds directories that contain a file named {directory_name}.skill.md.
"""

from pathlib import Path
from typing import List

from . import SkillMapping

from .base import DiscoveryStrategy
from ._common import discover_directory_skill


class DirectoryDiscovery(DiscoveryStrategy):
    """Find directory skills (subdirs with {dir_name}.skill.md)."""

    def discover(self) -> List[SkillMapping]:
        """Find all directory skills under source_path."""
        if not self.source_path.exists():
            return []

        if self.source_path.is_file():
            return []

        # If source itself is a directory skill, return just it.
        skill_md = discover_directory_skill(self.source_path)
        if skill_md is not None:
            return [
                self._create_mapping(
                    self.source_path,
                    self.source_path.name,
                    is_flat=False,
                    source_skill_md=skill_md,
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
                    self._create_mapping(
                        subdir,
                        subdir.name,
                        is_flat=False,
                        source_skill_md=skill_md,
                    )
                )

        return results
