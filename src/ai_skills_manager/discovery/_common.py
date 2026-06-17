"""Shared helpers for discovery strategies."""

from pathlib import Path
from typing import List, Optional


def find_skill_markdown(directory: Path) -> Optional[Path]:
    """Find a directory skill marker: {directory_name}.skill.md.

    Returns the path if exactly one matching *.skill.md file exists and it is
    named after the directory. Returns None otherwise.
    """
    expected_name = f"{directory.name}.skill.md"
    expected = directory / expected_name
    if expected.is_file():
        return expected
    return None


def collect_skill_markdowns(directory: Path) -> List[Path]:
    """Return all *.skill.md files under directory, sorted."""
    return sorted(p for p in directory.rglob("*.skill.md") if p.is_file())


def validate_directory_skill(directory: Path, skill_md: Path) -> None:
    """Ensure no other *.skill.md files exist in directory or its subdirs.

    Raises:
        ValueError: if another *.skill.md file is found.
    """
    for other in collect_skill_markdowns(directory):
        if other != skill_md:
            raise ValueError(
                f"Directory skill '{directory.name}' has extra skill file: {other}"
            )


def discover_directory_skill(directory: Path) -> Optional[Path]:
    """Validate and return the skill markdown for a directory skill.

    Returns the path to {directory_name}.skill.md if present and valid.
    Returns None if the directory is not a directory skill.
    Raises ValueError if the marker exists but extra *.skill.md files are found.
    """
    skill_md = find_skill_markdown(directory)
    if skill_md is None:
        return None
    validate_directory_skill(directory, skill_md)
    return skill_md
