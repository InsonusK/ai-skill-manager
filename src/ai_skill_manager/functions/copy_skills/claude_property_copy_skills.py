"""CopySkills decorator that additionally reshapes frontmatter for Claude Code.

Декоратор CopySkills, дополнительно приводящий frontmatter к формату Claude
Code.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import AbstractSet, Dict, TYPE_CHECKING

import yaml

from .abs_copy_skills import CopySkills
from ...entities import frontmatter as frontmatter_module

if TYPE_CHECKING:
    from ...entities.skill_v2 import Skill

logger = logging.getLogger(__name__)

# Frontmatter fields natively understood by Claude Code.
# Поля frontmatter, нативно понимаемые Claude Code.
NATIVE_FIELDS = {
    "name",
    "description",
    "when_to_use",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "hooks",
    "paths",
    "shell",
}


class ClaudePropertyCopySkills(CopySkills):
    """Wraps another ``CopySkills`` and reshapes each copy's frontmatter.

    Оборачивает другой ``CopySkills`` и приводит frontmatter каждой копии к
    нужному виду.

    Non-native frontmatter fields (and the legacy ``whenToUse`` alias) are
    moved out of the header into a ``## Metadata`` block in the body, so the
    file only declares fields Claude Code understands natively.

    Не нативные поля frontmatter (и устаревший алиас ``whenToUse``)
    переносятся из заголовка в блок ``## Metadata`` в теле файла, чтобы файл
    объявлял только поля, нативно понимаемые Claude Code.
    """

    def __init__(self, wrapped: CopySkills) -> None:
        """Initialize with the ``CopySkills`` to run before reshaping."""
        self._wrapped = wrapped

    def copy(
        self,
        skills: Dict[str, "Skill"],
        target_dir: Path,
        source_repo_path: Path,
        output_repo_path: Path,
        skip_names: AbstractSet[str] = frozenset(),
    ) -> Dict[str, Path]:
        """Copy via the wrapped implementation, then reshape non-skipped frontmatter."""
        copied_dirs = self._wrapped.copy(skills, target_dir, source_repo_path, output_repo_path, skip_names)
        for name, copied_dir in copied_dirs.items():
            if name in skip_names:
                continue
            self._reshape_frontmatter(copied_dir / "SKILL.md")
        return copied_dirs

    def _reshape_frontmatter(self, file_path: Path) -> None:
        """Move non-native frontmatter fields into a body ``## Metadata`` block."""
        content = file_path.read_text(encoding="utf-8")
        parsed, body = frontmatter_module.split(content)
        if parsed is None:
            return

        fm = dict(parsed)
        leftover: dict = {}

        when_to_use_value = fm.pop("whenToUse", None)
        if when_to_use_value is not None:
            if isinstance(when_to_use_value, list):
                when_to_use_value = ",".join(str(v) for v in when_to_use_value)
            if "when_to_use" not in fm:
                fm["when_to_use"] = when_to_use_value
            else:
                logger.warning(
                    "Skill %s has both 'whenToUse' and 'when_to_use' in "
                    "frontmatter; keeping 'when_to_use' and moving "
                    "'whenToUse' into the body metadata",
                    file_path,
                )
                leftover["whenToUse"] = when_to_use_value

        for key in list(fm.keys()):
            if key not in NATIVE_FIELDS:
                leftover[key] = fm.pop(key)

        if leftover:
            metadata_yaml = yaml.safe_dump(leftover, sort_keys=False, allow_unicode=True)
            body = f"{body}\n## Metadata\n\n```yaml\n{metadata_yaml}```\n"

        new_content = frontmatter_module.join(fm, body)
        if new_content != content:
            file_path.write_text(new_content, encoding="utf-8")
