from .link_kind import LinkKind


from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class LinkPath:
    """Processed path data for a link target.

    Обработанные данные пути для цели ссылки.

    Attributes:
        kind: Where the resolved link points.
            Куда ведёт разрешённая ссылка.
        formatted: Target path formatted for the link kind.
            Путь цели, приведённый к формату, соответствующему kind.
        repo_path: Path relative to the repository root. ``None`` for OS-absolute
            targets that live outside the repository.
            Путь относительно корня репозитория. ``None`` для OS-абсолютных
            целей за пределами репозитория.
        os_path: Absolute OS path to the target.
            Абсолютный путь ОС к цели.
        exists: Whether the target file exists on disk (including the
            ``.skill → .skill.md`` fallback).
            Существует ли целевой файл на диске (с учётом fallback
            ``.skill → .skill.md``).
        has_explicit_md_suffix: Whether the raw link path ended with an
            explicit ``.md`` suffix.
            Заканчивался ли исходный путь ссылки явным суффиксом ``.md``.
        is_inside_repo: Whether the target lies inside the repository root.
            Находится ли цель внутри корня репозитория.
    """

    kind: LinkKind
    formatted: str
    repo_path: Optional[str]
    os_path: Path
    exists: bool
    has_explicit_md_suffix: bool
    is_inside_repo: bool
