"""Pure helpers for classifying and resolving raw link path strings.

Чистые вспомогательные функции для классификации и разрешения сырых строк
путей ссылок.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

from ..entities.path_kind import PathKind

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)

_HTTP_SCHEMES = ("http://", "https://", "mailto:", "ftp://", "file://")


def is_http_link(path: str) -> bool:
    """Return ``True`` for web/mailto/ftp/file links.

    Возвращает ``True`` для web/mailto/ftp/file ссылок.

    Args:
        path: Link path to check. / Путь ссылки для проверки.
    """
    return path.lower().startswith(_HTTP_SCHEMES)


def split_fragment(path: str) -> Tuple[str, str]:
    """Split a path into path and ``#fragment`` parts.

    Разделить путь на часть пути и часть ``#fragment``.

    Args:
        path: Raw link path possibly containing ``#``. /
            Исходный путь ссылки, возможно содержащий ``#``.

    Returns:
        Tuple of (path_without_fragment, fragment_or_empty_string). /
        Кортеж (путь_без_фрагмента, фрагмент_или_пустая_строка).
    """
    if "#" in path:
        path_clean, header = path.split("#", 1)
        return path_clean, f"#{header}"
    return path, ""


def classify_raw_path(path: str) -> PathKind:
    """Classify a raw, non-web path string without any filesystem lookup.

    Классифицировать сырую, не веб-строку пути без обращения к файловой
    системе.

    Args:
        path: Clean link path without fragment. / Очищенный путь без фрагмента.

    Returns:
        The raw path kind. / Исходный вид пути.

    Raises:
        ValueError: If the path looks like a web URI.
            Если путь выглядит как веб-URI.
    """
    if is_http_link(path):
        raise ValueError(f"Web links are represented separately: {path}")
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


def existing_file(path: Path) -> Optional[Path]:
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
