"""Abstract base class for skill format patterns.

Абстрактный базовый класс для паттернов форматов навыков.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .....entities.skill_v2 import Skill


class absSkillTemplate(ABC):
    """Templates that can match a filesystem path to a skill.

    Subclasses implement matching rules for a single skill layout, such as
    ``*.skill.md`` files or directories containing ``SKILL.md``, and build a
    :class:`Skill` directly (reading its name from frontmatter) when a path
    matches.

    Шаблон, который может сопоставить путь файловой системы со скиллом.
    Подклассы реализуют правила сопоставления для одного расположения
    навыка, например файлы ``*.skill.md`` или директории, содержащие
    ``SKILL.md``, и строят :class:`Skill` напрямую (читая его имя из
    frontmatter), когда путь совпадает.
    """

    @property
    @abstractmethod
    def pattern_description(self) -> str:
        """Short human-readable description of what this pattern looks for.

        Returns:
            A pattern example such as ``{name}.skill.md`` or
            ``{name}/SKILL.md``.
        """
        ...

    @abstractmethod
    def match(self, path: Path) -> Optional[Skill]:
        """Return a Skill if the path matches this pattern.

        Return a Skill if the path matches this pattern.

        Вернуть Skill, если путь соответствует этому паттерну.

        Args:
            path: Filesystem path to check. / Путь файловой системы для проверки.

        Returns:
            A :class:`Skill` instance if matched, otherwise ``None``. /
            Экземпляр :class:`Skill` при совпадении, иначе ``None``.

        Raises:
            ValueError: If the path matches this pattern's shape but its
                frontmatter is missing a valid ``name``. /
                Если путь соответствует форме этого паттерна, но в его
                frontmatter отсутствует корректное ``name``.
        """
        ...
