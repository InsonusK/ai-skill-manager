"""Auto-discovery strategy.

Recursively scans a path (file or directory) and detects skills according to
registered flat and directory patterns.

Flat patterns (detected on files):
- HumanFlat: ``*.skill.md``

Directory patterns (detected on directories):
- Agent: directory contains ``SKILL.md``
- HumanDir: directory contains ``{dir_name}.skill.md``
"""

from pathlib import Path
from typing import List, Optional
from .base import SkillPattern, HumanDirPattern,HumanFlatPattern,AgentPattern
from ...models.skill import Skill
from .DiscoveryStrategy import DiscoveryStrategy


class AutoDiscovery(DiscoveryStrategy):
    """Recursively auto-detect skills of any supported format."""

    _FLAT_PATTERNS: List[SkillPattern] = [HumanFlatPattern()]
    _DIR_PATTERNS: List[SkillPattern] = [AgentPattern(), HumanDirPattern()]

    def discover(self) -> List[Skill]:
        """Recursively discover all skills."""
        if not self.source_path.exists():
            return []

        if self.source_path.is_file():
            return self._handle_file(self.source_path)

        return self._scan_directory(self.source_path)

    def _match_flat_patterns(self, path: Path) -> List[Skill]:
        """Return all flat-pattern matches for a file path."""
        return [
            skill
            for pattern in self._FLAT_PATTERNS
            if (skill := pattern.match(path)) is not None
        ]

    def _match_directory_patterns(self, path: Path) -> List[Skill]:
        """Return all directory-pattern matches for a directory path."""
        return [
            skill
            for pattern in self._DIR_PATTERNS
            if (skill := pattern.match(path)) is not None
        ]

    def _handle_file(self, filepath: Path) -> List[Skill]:
        """Handle a single file path."""
        matches = self._match_flat_patterns(filepath)

        if not matches:
            return []
        if len(matches) == 1:
            return matches

        raise ValueError(f"Skill definition conflict inFile {filepath}.\nCandidates: {[s.format.value for s in matches]} ")

    def _scan_directory(self, directory: Path) -> List[Skill]:
        """Recursively scan a directory for skills."""
        flat_matches: List[Skill] = []
        for file_path in sorted(directory.iterdir()):
            if file_path.is_file():
                flat_matches.extend(self._handle_file(file_path))

        dir_matches = self._match_directory_patterns(directory)

        # No directory skill here: collect flat files and recurse.
        if not dir_matches:
            results = list(flat_matches)
            results.extend(self._recurse_subdirectories(directory))
            return results

        if len(dir_matches) > 1:
            raise ValueError(
                f"Skill definition conflict in directory: {directory}.\nCandidates: {[s.format.value for s in dir_matches]}"
            )

        # Exactly one directory pattern matched.
        dir_skill = dir_matches[0]

        if not flat_matches:
            self._ensure_no_nested_skills(directory, dir_skill.file_path)
            return [dir_skill]

        if len(flat_matches) == 1:
            flat_skill = flat_matches[0]
            if dir_skill.file_path.resolve() == flat_skill.file_path.resolve():
                self._ensure_no_nested_skills(directory, dir_skill.file_path)
                return [dir_skill]
            raise ValueError(
                f"Cannot unambiguously determine skill in directory: {directory}\n.Candidates\n1. {dir_skill.file_path}\n2. {flat_skill.file_path}"
            )

        raise ValueError(
            f"Skill definition conflict in directory: {directory}"
        )

    def _recurse_subdirectories(self, directory: Path) -> List[Skill]:
        """Scan all subdirectories recursively."""
        results: List[Skill] = []
        for subdir in sorted(directory.iterdir()):
            if subdir.is_dir():
                results.extend(self._scan_directory(subdir))
        return results

    def _ensure_no_nested_skills(self, directory: Path, main_file: Path) -> None:
        """Ensure a directory skill does not contain nested skills."""
        main_file_resolved = main_file.resolve()
        for path in directory.rglob("*"):
            if path == directory:
                continue

            if path.is_file():
                for pattern in self._FLAT_PATTERNS:
                    if pattern.match(path) is not None:
                        if path.resolve() != main_file_resolved:
                            raise ValueError(
                                f"Nested skills detected in directory skill: {directory}"
                            )
            elif path.is_dir():
                if self._match_directory_patterns(path):
                    raise ValueError(
                        f"Nested skills detected in directory skill: {directory}"
                    )
