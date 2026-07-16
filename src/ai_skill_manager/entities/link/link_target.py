"""Where a link ultimately points.

Куда в итоге указывает ссылка.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class LinkTarget(ABC):
    """Base type for a resolved link target.

    Базовый тип для разрешённой цели ссылки.
    """


@dataclass(frozen=True, eq=True)
class SkillLinkTarget(LinkTarget):
    """A link that points inside a known skill.

    Ссылка, указывающая внутрь известного скилла.
    """

    skill_name: str
    """Name of the skill that owns the target file.
    Имя скилла, которому принадлежит целевой файл."""

    relative_path: Optional[Path]
    """Path of the target file relative to the skill's directory, or
    ``None`` when the target is the skill's own main file.
    Путь целевого файла относительно директории скилла, или ``None``,
    если цель - собственный основной файл скилла."""


@dataclass(frozen=True, eq=True)
class ExternalLinkTarget(LinkTarget):
    """A link that points at a file which is not part of any skill.

    Ссылка, указывающая на файл, не являющийся частью какого-либо скилла.
    """

    file_name: str
    """Name of the target file. / Имя целевого файла."""

    repo_absolute_path: Path
    """Path of the target file relative to the repository root.
    Путь целевого файла относительно корня репозитория."""
