"""Skill entity: identity plus its files.

Сущность скилла: идентичность и его файлы.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from .skill_kind import SkillKind
from .skill_name import is_kebab_case

if TYPE_CHECKING:
    from .skill_file_v2 import SkillFile


@dataclass(eq=True, unsafe_hash=True)
class Skill:
    """A discovered skill: its name, repo-absolute path, kind, and files.

    Обнаруженный скилл: имя, repo-absolute путь, тип и файлы.

    ``files`` starts empty and is filled in later by file discovery; it is
    excluded from equality/hash so a ``Skill`` can be used as a dict key
    (and its identity tracked) before enrichment completes.

    ``files`` изначально пуст и заполняется позже обнаружением файлов; он
    исключён из equality/hash, чтобы ``Skill`` можно было использовать как
    ключ словаря (и отслеживать его идентичность) до завершения обогащения.
    """

    name: str
    """Skill name, validated as kebab-case on construction.
    Имя скилла, проверяется как kebab-case при создании."""

    path: Path
    """Repo-absolute path: the file itself for a flat skill, the folder for
    a directory skill. / Repo-absolute путь: сам файл для плоского скилла,
    папка для скилла-директории."""

    kind: SkillKind
    """Whether the skill is a single file or a directory. / Является ли
    скилл единственным файлом или директорией."""

    main_file_relative_path: Optional[Path] = field(default=None, compare=False, hash=False)
    """For a directory skill, the path of its own entry file relative to
    ``path`` (e.g. ``web.skill.md``). ``None`` for a flat skill, where
    ``path`` already names the file directly.

    Для скилла-директории - путь его собственного основного файла
    относительно ``path`` (например, ``web.skill.md``). ``None`` для
    плоского скилла, где ``path`` уже прямо называет файл."""

    files: List["SkillFile"] = field(default_factory=list, compare=False, hash=False)
    """Files belonging to the skill, filled in by file discovery.
    Файлы, принадлежащие скиллу, заполняются обнаружением файлов."""

    def __post_init__(self) -> None:
        """Validate the skill name format.

        Проверяет формат имени скилла.
        """
        if not is_kebab_case(self.name):
            raise ValueError(f"Invalid skill name {self.name!r}: must be kebab-case")

    def is_main_file(self, relative_path: Optional[Path]) -> bool:
        """Return whether ``relative_path`` identifies this skill's own entry file.

        Возвращает, идентифицирует ли ``relative_path`` собственный
        основной файл этого скилла.
        """
        if self.kind is SkillKind.flat:
            return relative_path is None or relative_path == Path(".")
        return relative_path == self.main_file_relative_path
