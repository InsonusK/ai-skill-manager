"""SkillFile entity hierarchy: a file belonging to a skill.

Иерархия сущности SkillFile: файл, принадлежащий скиллу.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .link.file_link import FileLink


@dataclass(eq=True)
class SkillFile:
    """A file belonging to a skill, identified by its path relative to it.

    Файл, принадлежащий скиллу, идентифицируется путём относительно него.
    """

    name: str
    """File name (last path component). / Имя файла (последний компонент пути)."""

    path: Path
    """Path relative to the skill's directory. / Путь относительно директории скилла."""


@dataclass(eq=True)
class MarkdownSkillFile(SkillFile):
    """A markdown file, additionally holding its parsed links.

    Markdown-файл, дополнительно хранящий свои распарсенные ссылки.

    ``links`` starts empty and is filled in later by link discovery.
    ``links`` изначально пуст и заполняется позже обнаружением ссылок.
    """

    links: List["FileLink"] = field(default_factory=list, compare=False)
