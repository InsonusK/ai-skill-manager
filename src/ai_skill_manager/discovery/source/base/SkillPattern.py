"""Abstract base class for skill format patterns.

Абстрактный базовый класс для паттернов форматов навыков.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ....models import Skill, SkillFormat, Source


class SkillPattern(ABC):
    """Pattern that can match a filesystem path to a skill.

    Subclasses implement matching rules for a single skill format, such as
    ``*.skill.md`` files or directories containing ``SKILL.md``.

    Паттерн, который может сопоставить путь файловой системы с навыком.
    Подклассы реализуют правила сопоставления для одного формата навыка,
    например файлы ``*.skill.md`` или директории, содержащие ``SKILL.md``.
    """

    @property
    @abstractmethod
    def skill_format(self) -> SkillFormat:
        """Skill format produced by this pattern.

        Формат навыка, который производит этот паттерн.

        Returns:
            The :class:`SkillFormat` enum value for matches. /
            Значение перечисления :class:`SkillFormat` для совпадений.
        """
        ...

    @abstractmethod
    def match(
        self, path: Path, source: Source
    ) -> Optional[Skill]:
        """Return a Skill if the path matches this pattern.

        Вернуть Skill, если путь соответствует этому паттерну.

        Args:
            path: Filesystem path to check. / Путь файловой системы для проверки.
            source: Source metadata to attach to the skill. /
                Метаданные источника для навыка.

        Returns:
            A :class:`Skill` instance if matched, otherwise ``None``. /
            Экземпляр :class:`Skill` при совпадении, иначе ``None``.
        """
        ...
