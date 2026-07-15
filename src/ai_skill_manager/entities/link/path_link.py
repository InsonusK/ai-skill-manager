"""File-system path link model.

Модель файловой путевой ссылки.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, InitVar
from pathlib import Path
from typing import Optional

from ..path_kind import PathKind

from .abs_link import absLink

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PathRaw:
    """Raw path data as it appeared in the source link.

    Сырые данные пути, такие как они были в исходной ссылке.

    Attributes:
        path: The raw path string from the source.
            Сырая строка пути из источника.
        kind: The raw classification of the path.
            Классификация сырого пути.
    """

    path: str
    kind: PathKind


@dataclass(frozen=True)
class PathLink(absLink):
    """A link that points to a file inside the scanned source or on the OS.

    Ссылка, указывающая на файл внутри сканируемого источника или в файловой
    системе.

    Only the raw path and its shallow classification are stored here - actual
    target resolution is done later, against ``path_raw.path``, by
    ``entities.link.file_link_factory.FileLinkFactory``.

    Здесь хранится только сырой путь и его поверхностная классификация -
    настоящая резолюция цели выполняется позже, над ``path_raw.path``, в
    ``entities.link.file_link_factory.FileLinkFactory``.

    Attributes:
        path_raw: Raw path and its original classification.
            Сырой путь и его исходная классификация.
    """

    path_raw: PathRaw = field(init=False)

    raw_path: InitVar[str]
    header_value: InitVar[Optional[str]] = None
    is_image_value: InitVar[bool] = False

    def __post_init__(
        self,
        raw_path: str,
        header_value: Optional[str],
        is_image_value: bool,
    ) -> None:
        """Classify and store the raw path.

        Классифицировать и сохранить сырой путь.
        """
        object.__setattr__(self, "header", header_value)
        object.__setattr__(self, "is_image", is_image_value)

        raw_kind = _classify_raw_path(raw_path)
        object.__setattr__(self, "path_raw", PathRaw(path=raw_path, kind=raw_kind))


def _classify_raw_path(path: str) -> PathKind:
    """Classify a raw path string without doing any filesystem lookup.

    Классифицировать сырую строку пути без обращения к файловой системе.

    Args:
        path: Clean link path without fragment. / Очищенный путь без фрагмента.

    Returns:
        The raw path kind. / Исходный вид пути.

    Raises:
        ValueError: If the path looks like a web URI.
            Если путь выглядит как веб-URI.
    """
    lower = path.lower()
    if lower.startswith(("http://", "https://", "mailto:", "ftp://", "file://")):
        raise ValueError(f"Web links are represented by WebLink: {path}")
    # Normalize Windows path separators so links authored on Windows (e.g.
    # .\dir\file.md) are classified the same way as POSIX links.
    # Нормализуем Windows-разделители, чтобы ссылки, созданные на Windows,
    # классифицировались так же, как POSIX-ссылки.
    normalized = path.replace("\\", "/")
    if normalized.startswith(("./", "../")):
        logger.debug("Classified path %r as relative", path)
        return PathKind.relative
    if normalized.startswith("/"):
        logger.debug("Classified path %r as os_absolute", path)
        return PathKind.os_absolute
    # Windows drive-letter paths (C:/foo/bar) are OS-absolute as well.
    # Пути с буквой диска Windows (C:/foo/bar) тоже являются абсолютными путями ОС.
    if len(normalized) >= 2 and normalized[1] == ":":
        logger.debug("Classified path %r as os_absolute", path)
        return PathKind.os_absolute
    logger.debug("Classified path %r as repo_absolute", path)
    return PathKind.repo_absolute


def _existing_file(path: Path) -> Optional[Path]:
    """Return ``path`` if it exists, otherwise try the ``.md`` fallback.

    Вернуть ``path``, если он существует, иначе попробовать fallback ``.md``.

    This implements the rule that ``a-b-c.skill`` may mean ``a-b-c.skill.md``.

    Реализует правило, по которому ``a-b-c.skill`` может означать
    ``a-b-c.skill.md``.

    Args:
        path: Candidate absolute path. / Кандидат в абсолютный путь.

    Returns:
        The existing path, or ``None`` if neither variant exists.
        Существующий путь или ``None``, если ни один вариант не существует.
    """
    if path.exists():
        return path
    md_candidate = (
        path.with_suffix(path.suffix + ".md") if path.suffix else path.with_suffix(".md")
    )
    if md_candidate.exists():
        return md_candidate
    return None
