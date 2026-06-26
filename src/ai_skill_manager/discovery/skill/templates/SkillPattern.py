"""Abstract base class for skill format patterns.

Абстрактный базовый класс для паттернов форматов навыков.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ....entities import Skill, SkillFormat, Source


class absSkillTemplate(ABC):
    """Tempaltes that can match a filesystem path to a skill format.

    Subclasses implement matching rules for a single skill format, such as
    ``*.skill.md`` files or directories containing ``SKILL.md``.

    Шаблон, который может сопоставить путь файловой системы с форматом навыка.
    Подклассы реализуют правила сопоставления для одного формата навыка,
    например файлы ``*.skill.md`` или директории, содержащие ``SKILL.md``.
    """

    def __init__(self, source: Source, source_path: Path):
        """Initialize the pattern with source metadata.

        Initialize the pattern with source metadata.

        Инициализировать паттерн метаданными источника.

        Args:
            source: Source metadata to attach to matched skills. /
                Метаданные источника для прикрепления к совпавшим навыкам.
            source_path: Base path of the source being scanned. If it points
                to a single file, the parent directory is used instead. /
                Базовый путь сканируемого источника. Если он указывает на
                отдельный файл, используется родительская директория.
        """
        self._source = source
        # Skills always store a directory as their source_path. If a file path
        # is passed (e.g. GitHub subpath pointing to a single skill file), use
        # the containing directory.
        # Навыки всегда хранят директорию как source_path. Если передан путь к файлу
        # (например, подпуть GitHub, указывающий на один файл навыка),
        # используем содержащую директорию.
        self._source_path = source_path.parent if source_path.is_file() else source_path

    @property
    @abstractmethod
    def skill_format(self) -> SkillFormat:
        """Skill format produced by this pattern.

        Skill format produced by this pattern.

        Формат навыка, который производит этот паттерн.

        Returns:
            The :class:`SkillFormat` enum value for matches. /
            Значение перечисления :class:`SkillFormat` для совпадений.
        """
        ...

    @abstractmethod
    def match(
        self, path: Path
    ) -> Optional[Skill]:
        """Return a Skill if the path matches this pattern.

        Return a Skill if the path matches this pattern.

        Вернуть Skill, если путь соответствует этому паттерну.

        Args:
            path: Filesystem path to check. / Путь файловой системы для проверки.

        Returns:
            A :class:`Skill` instance if matched, otherwise ``None``. /
            Экземпляр :class:`Skill` при совпадении, иначе ``None``.
        """
        ...
