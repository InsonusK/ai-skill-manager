"""Skill format enumeration.

Перечисление форматов навыков.
"""

from __future__ import annotations
from enum import Enum


class SkillFormat(Enum):
    """Known layouts a skill can have on disk.

    Известные способы расположения навыка на диске.
    """

    Agent = "AgentSkill"
    """
    EN: AI agent format.
        - Standalone skill directory
        - Main file SKILL.md
        - Skill name equals directory name
    RU: Формат AI агента.
        - Отдельная директория со скилом
        - Основной файл SKILL.md
        - Название скила = название директории
    """

    HumanFlat = "HumanFlatSkill"
    """
    EN: Flat (single-file) skill.
        - One file named {skill name}.skill.md
        - Skill name = {skill name}
    RU: Плоский (одно файловый скилл).
        - Один файл с названием {skill name}.skill.md
        - Название скила = {skill name}
    """

    HumanDir = "HumanDirSkill"
    """
    EN: Directory skill.
        - Standalone skill directory
        - Main file {skill name}.skill.md
        - Directory name {skill name}.skill
        - Skill name = {skill name}
    RU: Директория со скилом.
        - Отдельная директория со скилом
        - Основной файл {skill name}.skill.md
        - Название директории {skill name}.skill
        - Название скила = {skill name}
    """

    @property
    def is_flat(self) -> bool:
        """Return ``True`` for the flat single-file format.

        Возвращает ``True`` для плоского однофайлового формата.
        """
        return self == SkillFormat.HumanFlat

    @property
    def is_dir(self) -> bool:
        """Return ``True`` for directory-based formats.

        Возвращает ``True`` для директорийных форматов.
        """
        return not self.is_flat
