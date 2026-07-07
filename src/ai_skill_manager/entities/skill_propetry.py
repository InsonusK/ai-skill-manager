"""Skill frontmatter property access.

Доступ к свойствам frontmatter навыка.
"""

from pathlib import Path
from typing import Any, Optional

from . import frontmatter


class SkillProperty:
    """Lazy reader for skill metadata stored in YAML frontmatter.

    Ленивый читатель метаданных навыка, хранящихся в YAML frontmatter.
    """

    def __init__(self, skill_path: Path):
        """Store the path and prepare a cache for parsed frontmatter.

        Сохраняет путь и подготавливает кеш для распарсенного frontmatter.
        """
        self.__skill_path = skill_path
        # EN: Cache for the parsed frontmatter dictionary.
        # RU: Кеш для словаря распарсенного frontmatter.
        self.__property_dict = None

    @property
    def all(self) -> dict[str, Any]:
        """Return all frontmatter properties, parsing them if needed.

        Возвращает все свойства frontmatter, распарсивая их при необходимости.
        """
        if self.__property_dict is None:
            self.__property_dict = SkillProperty._parse_frontmatter(self.__skill_path)
        return self.__property_dict

    @property
    def name(self) -> Optional[str]:
        """Return the skill name from frontmatter, or ``None`` if missing or invalid.

        Возвращает имя навыка из frontmatter или ``None``, если оно отсутствует или некорректно.
        """
        properties = self.all
        if properties is None:
            return None
        value = properties.get("name", None)
        if not isinstance(value, str):
            return None
        return value

    @staticmethod
    def _parse_frontmatter(file_path: Path) -> dict[str, Any] | None:
        """
        EN: Parse YAML frontmatter from a markdown file.
            Returns the parsed YAML dict, or None if no frontmatter found.
        RU: Распарсить YAML frontmatter из markdown-файла.
            Вернуть распарсенный YAML dict или None, если frontmatter не найден.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            return None

        parsed, _ = frontmatter.split(content)
        return parsed
