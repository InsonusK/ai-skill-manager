"""Auto-discovery strategy.

Recursively scans a directory:
- If directory contains {dir_name}.skill.md -> directory skill
- Otherwise -> treat *.skill.md files in this directory as flat skills and recurse
"""

from pathlib import Path
from typing import List

from .base import DiscoveryStrategy, SkillMapping, is_skill_md, skill_name_from_file
from ._common import discover_directory_skill


class AutoDiscovery(DiscoveryStrategy):
    """Auto-detect skill type for each directory/file."""

    def discover(self) -> List[SkillMapping]:
        """Recursively discover all skills."""
        if not self.source_path.exists():
            return []

        if self.source_path.is_file():
            return self._handle_file(self.source_path)

        return self._scan_directory(self.source_path)

    def _handle_file(self, filepath: Path) -> List[SkillMapping]:
        """Handle a single file."""
        if is_skill_md(filepath):
            return [
                self._create_mapping(
                    filepath,
                    skill_name_from_file(filepath),
                    is_flat=True,
                    source_skill_md=filepath,
                )
            ]
        return []

    def _scan_directory(self, directory: Path) -> List[SkillMapping]:
        """Recursively scan directory for skills."""
        results = []

        # Directory skill takes precedence.
        skill_md = discover_directory_skill(directory)
        if skill_md is not None:
            return [
                self._create_mapping(
                    directory,
                    directory.name,
                    is_flat=False,
                    source_skill_md=skill_md,
                )
            ]

        # Flat: collect *.skill.md files directly in this directory.
        for skill_file in sorted(directory.glob("*.skill.md")):
            results.append(
                self._create_mapping(
                    skill_file,
                    skill_name_from_file(skill_file),
                    is_flat=True,
                    source_skill_md=skill_file,
                )
            )

        # Recurse into subdirectories.
        for subdir in sorted(directory.iterdir()):
            if subdir.is_dir():
                results.extend(self._scan_directory(subdir))

        return results
