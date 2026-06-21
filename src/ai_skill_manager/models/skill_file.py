"""Skill file model with lazy link loading.

Модель файла скила с ленивой загрузкой ссылок.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

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

    path: Path
    _links: Tuple[Link] = field(
        default=None, init=False, repr=False, compare=False, hash=False
    )

    @property
    def links(self) -> Tuple[Link]:
        """Return all parsed links in this file.

        Вернуть все распарсенные ссылки в этом файле.

        Returns:
            Parsed links in source order.
            Распарсенные ссылки в порядке следования в исходнике.
        """
        if self._links is None:
            from ..adapters.link_updater.factory.link_factory import LinkFactory

            object.__setattr__(
                self,
                "_links",
                tuple(LinkFactory().create_links_for_path(self.path)),
            )
        return self._links
