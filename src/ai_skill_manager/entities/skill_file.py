"""Skill file model with lazy link loading.

Модель файла скила с ленивой загрузкой ссылок.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

from ..discovery.link import search_links_in_content

from .link import Link


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
    """
    class Context:
        links: Optional[Tuple[Link]] = None
        
    path: Path
    """absolute path to skill file / абсолютный путь к файлу навыка"""
    __context: Context = field(init=False, compare=False, hash=False, default_factory=Context)
    

    def __post_init__(self):
        """Validate that the stored path is an absolute file path.

        Проверяет, что сохранённый путь является абсолютным путём к файлу.
        """
        assert self.path.is_absolute(), f"Skill file path must be absolute. Current value: {self.path}"
        assert self.path.is_file(), f"Skill file path must lead to file. Now it leads to {self.path}"

    @property
    def links(self) -> Tuple[Link]:
        """Return all parsed links in this file.

        Вернуть все распарсенные ссылки в этом файле.

        Returns:
            Parsed links in source order.
            Распарсенные ссылки в порядке следования в исходнике.
        """
        # EN: Parse links lazily and cache them in the frozen dataclass.
        # RU: Лениво парсим ссылки и кешируем их в замороженном dataclass.
        if self.__context.links is None:
            self.__context.links = tuple(search_links_in_content(self.content))
        return self.__context.links

    @property
    def content(self) -> str:
        """Return the file content, reading from disk when not provided.

        Возвращает содержимое файла, читая его с диска при необходимости.
        """
        return self.path.read_text(encoding="utf-8")
