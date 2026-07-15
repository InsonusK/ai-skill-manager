"""Copy one skill's own files into the target directory.

Копирование собственных файлов одного скилла в целевую директорию.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from ..entities.skill_kind import SkillKind

if TYPE_CHECKING:
    from ..entities.skill_v2 import Skill


class SkillFileCopier:
    """Copies a skill's files into ``{target_dir}/{skill.name}/``.

    Копирует файлы скилла в ``{target_dir}/{skill.name}/``.

    The skill's own main file is always written as ``SKILL.md``; every
    other file keeps its relative path.

    Собственный основной файл скилла всегда записывается как ``SKILL.md``;
    все остальные файлы сохраняют свой относительный путь.
    """

    def copy(self, skill: "Skill", target_dir: Path) -> Path:
        """Copy ``skill``'s files and return its new directory.

        Копирует файлы ``skill`` и возвращает его новую директорию.
        """
        skill_target_dir = target_dir / skill.name
        skill_target_dir.mkdir(parents=True, exist_ok=True)

        for skill_file in skill.files:
            source = skill.path if skill.kind is SkillKind.flat else skill.path / skill_file.path
            destination = (
                skill_target_dir / "SKILL.md"
                if skill.is_main_file(skill_file.path)
                else skill_target_dir / skill_file.path
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        return skill_target_dir
