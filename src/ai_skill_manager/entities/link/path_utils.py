"""Cross-platform path helpers for link resolution.

Вспомогательные функции для кроссплатформенного разрешения путей ссылок.
"""

from __future__ import annotations

import os
from pathlib import Path


def normalize_path(path: Path) -> Path:
    """Return a canonical, comparable form of ``path``.

    Returns the resolved path when the filesystem entry exists, otherwise
    falls back to a normalized absolute path. This avoids false negatives
    caused by Windows short names (``RUNNER~1``) vs long names
    (``runneradmin``) or by redundant ``.``/``..`` segments.

    Возвращает каноническую, сравнимую форму пути. Если объект файловой
    системы существует, используется ``Path.resolve()``, иначе — нормализованный
    абсолютный путь. Это исключает ложные несовпадения из-за Windows-коротких
    имён, длинных имён или лишних сегментов ``.``/``..``.
    """
    try:
        return path.resolve()
    except OSError:
        return Path(os.path.normpath(path)).absolute()


def same_path(a: Path, b: Path) -> bool:
    """Return ``True`` if ``a`` and ``b`` denote the same filesystem path.

    Сравнивает пути через :func:`normalize_path`, чтобы Windows-короткие
    и длинные имена считались равными.
    """
    return normalize_path(a) == normalize_path(b)


def is_relative_to_resolved(child: Path, parent: Path) -> bool:
    """Return ``True`` if ``child`` is inside ``parent`` after normalization.

    Использует нормализованные пути, чтобы корректно работать на Windows,
    где один и тот же путь может быть представлен через короткое или длинное имя.
    """
    try:
        normalize_path(child).relative_to(normalize_path(parent))
        return True
    except ValueError:
        return False
