"""File-system path link model.

Модель файловой путевой ссылки.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, InitVar
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from ..link_kind import LinkKind
from .absLink import absLink

if TYPE_CHECKING:
    from ...entities.skill import Skill
    from ...entities.skill_file import SkillFile


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
    kind: LinkKind


@dataclass(frozen=True)
class PathInfo:
    """Processed path data for a file-system link.

    Обработанные данные пути для файловой ссылки.

    Attributes:
        kind: The resolved link kind. A raw link first tries to become
            ``relative`` (inside the skill folder), otherwise ``repo_absolute``.
            Разрешённый вид ссылки. Ссылка из ``raw`` сначала пытается стать
            ``relative`` (внутри папки скилла), иначе — ``repo_absolute``.
        formatted: The path written in the format of ``kind``.
            Путь в формате, соответствующем ``kind``.
        repo_path: The path relative to ``ScanLocation.repo_path``.
            Путь относительно ``ScanLocation.repo_path``.
        os_path: The absolute OS path resolved from the raw link.
            Абсолютный путь в ОС, разрешённый из сырой ссылки.
        exists: ``True`` when the target file exists, including after the
            ``.skill`` -> ``.skill.md`` fallback.
            ``True``, когда целевой файл существует, включая fallback
            ``.skill`` -> ``.skill.md``.
    """

    kind: LinkKind
    formatted: str
    repo_path: str
    os_path: Path
    exists: bool


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
        path: Processed path resolved against the skill and repository.
            Обработанный путь, разрешённый относительно скилла и репозитория.
    """

    path_raw: PathRaw = field(init=False)
    path: PathInfo = field(init=False)

    skill_file: InitVar["SkillFile"]
    raw_path: InitVar[str]
    header_value: InitVar[Optional[str]] = None
    is_image_value: InitVar[bool] = False

    def __post_init__(
        self,
        skill_file: "SkillFile",
        raw_path: str,
        header_value: Optional[str],
        is_image_value: bool,
    ) -> None:
        """Resolve the raw path against the skill and repository.

        Разрешить сырой путь относительно скилла и репозитория.
        """
        object.__setattr__(self, "header", header_value)
        object.__setattr__(self, "is_image", is_image_value)

        raw_kind = _classify_raw_path(raw_path)
        path_info = _resolve_path(skill_file, raw_path, raw_kind)
        object.__setattr__(self, "path_raw", PathRaw(path=raw_path, kind=raw_kind))
        object.__setattr__(self, "path", path_info)

    @property
    def target(self) -> str:
        """Return the formatted path target.

        Вернуть форматированную цель пути.
        """
        return self.path.formatted

def _classify_raw_path(path: str) -> LinkKind:
    """Classify a raw path string without doing any filesystem lookup.

    Классифицировать сырую строку пути без обращения к файловой системе.

    Args:
        path: Clean link path without fragment. / Очищенный путь без фрагмента.

    Returns:
        The raw link kind. / Исходный вид ссылки.

    Raises:
        ValueError: If the path looks like a web URI.
            Если путь выглядит как веб-URI.
    """
    lower = path.lower()
    if lower.startswith(("http://", "https://", "mailto:", "ftp://", "file://")):
        raise ValueError(f"Web links are represented by WebLink: {path}")
    if path.startswith(("./", "../")):
        return LinkKind.relative
    if path.startswith("/"):
        return LinkKind.os_absolute
    return LinkKind.repo_absolute


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
    raw_kind: LinkKind,
) -> PathInfo:
    """Resolve a raw path to a :class:`PathInfo`.

    Разрешить сырой путь в :class:`PathInfo`.

    The resolution order matches the user specification: a raw link first
    attempts to become ``relative`` (inside the skill folder), otherwise it is
    treated as ``repo_absolute``. OS-absolute raw paths are not applicable for
    skill links and are normalised to repo-absolute resolution.

    Порядок разрешения соответствует спецификации: ссылка из ``raw`` сначала
    пытается стать ``relative`` (внутри папки скилла), иначе считается
    ``repo_absolute``. Абсолютные пути ОС для скилловых ссылок не применимы и
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
        return PathInfo(
            kind=LinkKind.relative,
            formatted="./" + file_path.name,
            repo_path=repo_relative,
            os_path=resolved,
            exists=True,
        )

    if raw_kind == LinkKind.relative:
        candidate = (file_path.parent / raw_path).resolve()
    elif raw_kind == LinkKind.repo_absolute:
        candidate = (repo_path / raw_path).resolve()
    elif raw_kind == LinkKind.os_absolute:
        # Normalize leading slash to repo-root resolution.
        # Нормализуем ведущий слеш к разрешению от корня репозитория.
        normalized = raw_path.lstrip("/")
        candidate = (repo_path / normalized).resolve() if normalized else repo_path.resolve()
    else:
        raise ValueError(f"Unknown raw link kind: {raw_kind}")

    target = _existing_file(candidate)
    resolved = target if target is not None else candidate

    if not resolved.is_relative_to(repo_path):
        raise ValueError(
            f"Link target {resolved.as_posix()!r} is outside the repository root "
            f"{repo_path.as_posix()!r}"
        )

    folder = skill.folder_path
    is_self_link = target is not None and target == skill.file_path
    is_inside_skill_folder = (
        target is not None and folder is not None and target.is_relative_to(folder)
    )

    if is_self_link or is_inside_skill_folder:
        kind = LinkKind.relative
        if is_self_link:
            formatted = "./" + skill.file_path.name
        else:
            formatted = "./" + target.relative_to(folder).as_posix()
    else:
        kind = LinkKind.repo_absolute
        formatted = Path(os.path.relpath(resolved, repo_path)).as_posix()

    repo_relative = Path(os.path.relpath(resolved, repo_path)).as_posix()

    return PathInfo(
        kind=kind,
        formatted=formatted,
        repo_path=repo_relative,
        os_path=resolved,
        exists=target is not None,
    )
