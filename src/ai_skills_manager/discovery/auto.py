"""Auto-discovery strategy.

Recursively scans directory:
- If directory contains SKILL.md -> directory skill
- Otherwise -> flat: each .md becomes skill, recurse into subdirs
"""

from pathlib import Path
from typing import List

from .base import DiscoveryStrategy, SkillMapping


class AutoDiscovery(DiscoveryStrategy):
    """Auto-detect skill type for each directory/file."""

    def discover(self) -> List[SkillMapping]:
        """Recursively discover all skills."""
        if not self.source_path.exists():
            return []

        if self.source_path.is_file():
            return self._handle_file(self.source_path)

        return self._scan_directory(self.source_path, prefix="")

    def _handle_file(self, filepath: Path) -> List[SkillMapping]:
        """Handle a single file."""
        if filepath.suffix == '.md':
            name = filepath.stem
            if filepath.name.endswith('.skill.md'):
                name = filepath.name[:-9]
            return [self._create_mapping(filepath, name, is_flat=True)]
        return []

    def _scan_directory(self, directory: Path, prefix: str) -> List[SkillMapping]:
        """Recursively scan directory for skills."""
        results = []
        dir_name = directory.name

        # Check if this directory itself is a skill
        if (directory / 'SKILL.md').exists():
            # Directory skills use their own name, no prefix
            results.append(self._create_mapping(directory, dir_name, is_flat=False))
            return results

        # Check if there is a file named dir_name.skill.md
        if (directory / f"{dir_name}.skill.md").exists():
            results.append(self._create_mapping(directory, dir_name, is_flat=False))
            return results

        # Flat: collect .md files
        for md_file in sorted(directory.glob('*.md')):
            if md_file.name.endswith('.skill.md'):
                name = md_file.name[:-9]
            else:
                name = md_file.stem
            name = prefix + name if prefix else name
            results.append(self._create_mapping(md_file, name, is_flat=True))

        # Recurse into subdirectories
        for subdir in sorted(directory.iterdir()):
            if subdir.is_dir():
                new_prefix = f"{prefix}{subdir.name}-" if prefix else f"{subdir.name}-"
                results.extend(self._scan_directory(subdir, new_prefix))

        return results
