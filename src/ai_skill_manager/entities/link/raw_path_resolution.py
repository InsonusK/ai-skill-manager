"""Resolve a raw link path string to an OS-absolute path.

Разрешение строки сырого пути ссылки в OS-absolute путь.
"""

from __future__ import annotations

from pathlib import Path

from ..path_kind import PathKind
from .path_link import _classify_raw_path, _existing_file


def resolve_raw_link_path(raw_path: str, file_absolute_path: Path, repo_path: Path) -> Path:
    """Resolve ``raw_path`` (as written in a link) to an OS-absolute path.

    Reuses the same raw-path classification and ``.md``-suffix fallback as
    the existing link parser, so a relative/repo-absolute/OS-absolute raw
    path resolves identically here and during validation.

    Разрешает ``raw_path`` (как он написан в ссылке) в OS-absolute путь.
    Переиспользует ту же классификацию сырого пути и fallback на суффикс
    ``.md``, что и существующий парсер ссылок, поэтому относительный,
    repo-absolute или OS-absolute сырой путь разрешается здесь так же, как
    и при валидации.

    Args:
        raw_path: The link target exactly as written (no fragment).
            / Цель ссылки в точности как она написана (без фрагмента).
        file_absolute_path: Absolute path of the file containing the link,
            used to resolve relative raw paths.
            / Абсолютный путь файла, содержащего ссылку, используется для
            разрешения относительных сырых путей.
        repo_path: Absolute path to the repository root, used to resolve
            repo-absolute raw paths.
            / Абсолютный путь к корню репозитория, используется для
            разрешения repo-absolute сырых путей.

    Returns:
        The resolved absolute path. Does not raise if the target does not
        exist - callers decide what a missing target means.
        / Разрешённый абсолютный путь. Не выбрасывает исключение, если цель
        не существует - вызывающая сторона решает, что означает
        отсутствующая цель.
    """
    normalized_raw_path = raw_path.replace("\\", "/")
    kind = _classify_raw_path(normalized_raw_path)

    if kind == PathKind.relative:
        candidate = (file_absolute_path.parent / normalized_raw_path).resolve()
    elif kind == PathKind.repo_absolute:
        candidate = (repo_path / normalized_raw_path).resolve()
    elif kind == PathKind.os_absolute:
        candidate = Path(raw_path).resolve()
    else:
        raise ValueError(f"Unknown raw path kind: {kind}")

    existing = _existing_file(candidate)
    return existing if existing is not None else candidate
