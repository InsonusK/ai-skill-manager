"""File-system path link model.

Модель файловой путевой ссылки.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, InitVar
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .link_path import LinkPath

from ..path_kind import PathKind

from .link_kind import LinkKind
from .abs_link import absLink

if TYPE_CHECKING:
    from ..skill import Skill
    from ..skill_file import SkillFile


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
    """A link that points to a file inside the scanned source.

    Ссылка, указывающая на файл внутри сканируемого источника.

    The constructor requires a :class:`SkillFile` because resolving a path link
    needs the owning skill, the file path and the repository root.

    Конструктору требуется :class:`SkillFile`, потому что для разрешения
    путевой ссылки нужен владеющий скилл, путь к файлу и корень репозитория.

    Attributes:
        path_raw: Raw path and its original classification.
            Сырой путь и его исходная классификация.
    """

    path_raw: PathRaw = field(init=False)

    skill_file_value: InitVar["SkillFile"]
    raw_path: InitVar[str]
    header_value: InitVar[Optional[str]] = None
    is_image_value: InitVar[bool] = False

    def __post_init__(
        self,
        skill_file_value: "SkillFile",
        raw_path: str,
        header_value: Optional[str],
        is_image_value: bool,
    ) -> None:
        """Resolve the raw path against the skill and repository.

        Разрешить сырой путь относительно скилла и репозитория.
        """
        object.__setattr__(self, "header", header_value)
        object.__setattr__(self, "is_image", is_image_value)
        object.__setattr__(self, "skill_file", skill_file_value)

        raw_kind = _classify_raw_path(raw_path)
        path_info = _resolve_path(skill_file_value, raw_path, raw_kind)

        object.__setattr__(self, "path_raw", PathRaw(path=raw_path, kind=raw_kind))
        #object.__setattr__(self, "kind", path_info.kind)
        object.__setattr__(self, "path", path_info)


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
    if path.startswith(("./", "../")):
        return PathKind.relative
    if path.startswith("/"):
        return PathKind.os_absolute
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


def _resolve_path(
    skill_file: "SkillFile",
    raw_path: str,
    raw_kind: PathKind,
) -> LinkPath:
    """Resolve a raw path to a :class:`PathInfo`.

    Разрешить сырой путь в :class:`PathInfo`.

    The resolution order matches the user specification: a raw link first
    attempts to become ``skill`` (inside the skill folder), otherwise it is
    treated as ``source`` (inside the repository but outside the skill).
    OS-absolute raw paths are normalised to repo-root resolution.

    Порядок разрешения соответствует спецификации: сырая ссылка сначала
    пытается стать ``skill`` (внутри папки скилла), иначе считается
    ``source`` (внутри репозитория, но вне скилла). Абсолютные пути ОС
    нормализуются к разрешению от корня репозитория.
    """
    skill = skill_file.skill
    file_path = skill_file.path
    repo_path = skill.source.get_scan_location().repo_path

    # A fragment-only link (e.g. [[#header]]) points to the containing skill file.
    # Ссылка только на фрагмент (например, [[#заголовок]]) указывает на файл скилла.
    if raw_path == "":
        resolved = file_path.resolve()
        repo_relative = Path(os.path.relpath(resolved, repo_path)).as_posix()
        return LinkPath(
            kind=LinkKind.skill,
            formatted="./" + file_path.name,
            repo_path=repo_relative,
            os_path=resolved,
        )

    if raw_kind == PathKind.relative:
        candidate = (file_path.parent / raw_path).resolve()
    elif raw_kind == PathKind.repo_absolute:
        candidate = (repo_path / raw_path).resolve()
    elif raw_kind == PathKind.os_absolute:
        # Normalize leading slash to repo-root resolution.
        # Нормализуем ведущий слеш к разрешению от корня репозитория.
        normalized = raw_path.lstrip("/")
        candidate = (repo_path / normalized).resolve() if normalized else repo_path.resolve()
    else:
        raise ValueError(f"Unknown raw path kind: {raw_kind}")

    target = _existing_file(candidate)
    resolved = target if target is not None else candidate

    if not resolved.is_relative_to(repo_path):
        raise ValueError(
            f"Link target {resolved.as_posix()!r} is outside the repository root "
            f"{repo_path.as_posix()!r}"
        )

    folder = skill.folder_path
    is_self_link = resolved == skill.file_path
    is_inside_skill_folder = folder is not None and resolved.is_relative_to(folder)

    repo_relative = Path(os.path.relpath(resolved, repo_path)).as_posix()

    if is_self_link or is_inside_skill_folder:
        kind = LinkKind.skill
        if is_self_link:
            formatted = "./" + skill.file_path.name
        else:
            formatted = "./" + resolved.relative_to(folder).as_posix()
    else:
        kind = LinkKind.source
        formatted = repo_relative

    return LinkPath(
        kind=kind,
        formatted=formatted,
        repo_path=repo_relative,
        os_path=resolved,
    )
