"""Skill file model with lazy link loading.

Модель файла скила с ленивой загрузкой ссылок.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple

from .link import absLink

if TYPE_CHECKING:
    from .skill import Skill


@dataclass(frozen=True)
class SkillFile:
    """A single markdown file that belongs to a skill.

    Parses and caches links on first access so the same links can be reused by
    validators and the sync replacer without parsing the file twice.

    Один markdown-файл, принадлежащий скиллу. Парсит и кеширует ссылки при
    первом обращении, чтобы одни и те же ссылки можно было использовать
    валидатором и синхронизатором без повторного парсинга файла.

    Attributes:
        path: Path to the markdown file on disk.
            Путь к markdown-файлу на диске.
        skill: Skill that owns this file. Not used for equality/hashing.
            Скилл, которому принадлежит файл. Не участвует в сравнении и хеше.
    """

    class Context:
        links: Optional[Tuple[absLink, ...]] = None

    path: Path
    """absolute path to skill file / абсолютный путь к файлу навыка"""
    skill: "Skill" = field(compare=False, hash=False)
    """owning skill / владеющий скилл"""
    __context: Context = field(init=False, compare=False, hash=False, default_factory=Context)

    def __post_init__(self):
        """Validate that the stored path is an absolute file path.

        Проверяет, что сохранённый путь является абсолютным путём к файлу.
        """
        # EN: Resolve the path so it matches the canonical form used by Skill
        # (long names on Windows, no redundant segments).
        # RU: Приводим путь к каноническому виду, используемому Skill
        # (длинные имена на Windows, без лишних сегментов).
        object.__setattr__(self, "path", self.path.resolve())
        assert self.path.is_absolute(), f"Skill file path must be absolute. Current value: {self.path}"
        assert self.path.is_file(), f"Skill file path must lead to file. Now it leads to {self.path}"

    @property
    def links(self) -> Tuple[absLink, ...]:
        """Return all parsed links in this file.

        Вернуть все распарсенные ссылки в этом файле.

        Returns:
            Parsed links in source order.
            Распарсенные ссылки в порядке следования в исходнике.
        """
        # EN: Parse links lazily and cache them in the frozen dataclass.
        # RU: Лениво парсим ссылки и кешируем их в замороженном dataclass.
        if self.__context.links is None:
            # Local import avoids a circular dependency between entities and discovery.
            # Локальный импорт позволяет избежать циклической зависимости между entities и discovery.
            from ..discovery.link import search_links_in_content

            self.__context.links = tuple(search_links_in_content(self.content))
        return self.__context.links

    @property
    def content(self) -> str:
        """Return the file content, reading from disk when not provided.

        Возвращает содержимое файла, читая его с диска при необходимости.
        """
        return self.path.read_text(encoding="utf-8")
