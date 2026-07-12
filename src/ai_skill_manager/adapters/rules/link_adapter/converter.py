"""Link converters for the agent skill-link format.

Конвертеры ссылок в формат агентских skill-link.
"""

from __future__ import annotations

import logging
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from ....entities import LinkKind, absLink
from ....entities.link.path_utils import is_relative_to_resolved, same_path

if TYPE_CHECKING:
    from ....entities import Skill

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


def _append_header(target: str, header: Optional[str]) -> str:
    """Append the optional ``#fragment`` to a target string.

    Args:
        target: Base link target.
            Базовая цель ссылки.
        header: Optional fragment, e.g. ``#section``.
            Опциональный фрагмент, например ``#section``.

    Returns:
        Target with fragment appended when present.
            Цель с добавленным фрагментом, если он есть.
    """
    if header:
        return f"{target}{header}"
    return target


def _repo_absolute_path(os_path: Path, repo_path: Path) -> str:
    """Return ``os_path`` relative to the repository root as a POSIX path.

    The result is the ``repo_absolute`` link format: a path starting from the
    repository root without a leading ``./``.

    Args:
        os_path: Absolute target path inside the repository.
            Абсолютный путь цели внутри репозитория.
        repo_path: Absolute path to the repository root.
            Абсолютный путь к корню репозитория.

    Returns:
        Repository-relative POSIX path.
            Путь относительно корня репозитория в POSIX-формате.
    """
    logger.debug("Computing repo-absolute path: os_path=%s repo_path=%s", os_path, repo_path)
    return Path(os.path.relpath(os_path, repo_path)).as_posix()


def _default_repo_path(link: absLink) -> Path:
    """Fall back to the link's own skill's repo path when none is supplied.

    Used only by call sites (mostly tests) that resolve a link without going
    through a real sync run, where the link's owning skill already sits at
    its final location.

    Используется только вызывающими сторонами (в основном тестами), которые
    разрешают ссылку без реального прогона синхронизации, где скилл, которому
    принадлежит ссылка, уже находится в своём итоговом расположении.
    """
    return link.skill_file.skill.source.get_scan_location().repo_path


def _finalize_target(
    new_skill: Skill,
    rel: Optional[Path],
    is_main: bool,
    repo_path: Path,
    target_dir: Optional[Path],
) -> str:
    """Build the repo-absolute link string for a location inside ``new_skill``.

    Формирует строку repo-absolute ссылки для расположения внутри ``new_skill``.

    When ``target_dir`` is known, the string is built purely from the
    skill's *name* and the sync's directory layout (``target_dir`` relative
    to ``repo_path``) - never from ``new_skill``'s own ``folder_path``. This
    matters because during materialization a skill's bytes may still be
    sitting in a staging directory rather than its final location; the link
    text written into those bytes must reflect where the skill will end up,
    not where it currently physically is.

    Falls back to ``new_skill``'s own (real) ``folder_path``/``file_path``
    when ``target_dir`` is not supplied - used by callers that resolve a
    link directly against an already-final skill (e.g. unit tests).

    Когда ``target_dir`` известен, строка строится исключительно из *имени*
    скилла и раскладки директорий синка (``target_dir`` относительно
    ``repo_path``) - никогда из собственного ``folder_path`` у ``new_skill``.
    Это важно, потому что во время материализации байты скилла могут всё ещё
    находиться в staging-директории, а не в итоговом расположении; текст
    ссылки, записываемый в эти байты, должен отражать, где скилл окажется, а
    не где он находится физически сейчас.

    При отсутствии ``target_dir`` используется собственный (реальный)
    ``folder_path``/``file_path`` у ``new_skill`` - для вызывающих сторон,
    которые разрешают ссылку напрямую относительно уже финального скилла
    (например, юнит-тесты).
    """
    if target_dir is not None:
        offset = Path(os.path.relpath(target_dir, repo_path))
        skill_root = offset / new_skill.properties.name
        final = skill_root / "SKILL.md" if is_main else skill_root / rel
        return final.as_posix()

    final_path = new_skill.file_path if is_main else new_skill.folder_path / rel
    return _repo_absolute_path(final_path, repo_path)


class absLinkConverter(ABC):
    """Abstract converter from :class:`absLink` to agent skill-link target string.

    Абстрактный конвертер из :class:`absLink` в строку цели агентской skill-link.
    """

    @abstractmethod
    def convert(
        self,
        link: absLink,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]] = None,
        **kwargs,
    ) -> str:
        """Convert a link to the agent skill-link format.

        Преобразует ссылку в формат агентской skill-link.

        Args:
            link: The parsed link to convert.
                Распарсенная ссылка для преобразования.
            skills: All known *source* skills for resolving cross-skill links.
                Все известные *исходные* навыки для разрешения меж-скилловых ссылок.
            skill_mapping: Mapping from original source skill to its current
                location this run. Used to translate a resolved source-skill
                identity into the path the link should ultimately point at.
                / Отображение исходного скилла в его текущее расположение в
                этом запуске. Используется, чтобы перевести разрешённую
                идентичность исходного скилла в путь, на который должна
                указывать ссылка.

        Returns:
            The new link target string.
                Новая строка цели ссылки.
        """
        ...


class SkillLinkConverter(absLinkConverter):
    """Converts links that point inside the current skill.

    Для ссылок, которые указывают внутрь текущего скилла.

    Resolution is anchored on the link's *owning* skill (``link.skill_file.skill``),
    which - as long as the caller feeds this converter links parsed from the
    original source files - is always the true source skill, never a guess
    derived from a copied path.

    Резолюция опирается на скилл-владелец ссылки (``link.skill_file.skill``),
    который - пока вызывающая сторона передаёт этому конвертеру ссылки,
    распарсенные из исходных файлов - всегда является настоящим исходным
    скиллом, а не догадкой, выведенной из скопированного пути.
    """

    def convert(
        self,
        link: absLink,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]] = None,
        repo_path: Optional[Path] = None,
        target_dir: Optional[Path] = None,
        **kwargs,
    ) -> str:
        """Return the repo-absolute path to the target, preserving any header."""
        old_skill = link.skill_file.skill
        new_skill = (skill_mapping or {}).get(old_skill, old_skill)
        target_path = link.path.os_path

        is_main = old_skill.folder_path is None or same_path(target_path, old_skill.file_path)
        rel = None if is_main else target_path.relative_to(old_skill.folder_path)

        effective_repo_path = repo_path if repo_path is not None else _default_repo_path(link)
        target = _finalize_target(new_skill, rel, is_main, effective_repo_path, target_dir)
        return _append_header(target, link.header)


class ExternalLinkConverter(absLinkConverter):
    """Converts external links (web, mailto, etc.).

    Для внешних ссылок (web, mailto и т.д.).
    """

    def convert(
        self,
        link: absLink,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]] = None,
        **kwargs,
    ) -> str:
        """Return the external URL unchanged, preserving any header."""
        # EN: External links are kept as-is.
        # RU: Внешние ссылки оставляем без изменений.
        return _append_header(link.path.formatted, link.header)


class ExternalFileConverter:
    """Copies a non-skill file or directory into ``files/`` and returns the relative link.

    Копирует файл или директорию, не принадлежащие скиллу, в ``files/`` и
    возвращает относительную ссылку.
    """

    def __init__(self, copied_files: Dict[Path, Path]):
        """Initialize with a shared copy registry.

        Args:
            copied_files: Maps original source path -> copied target path.
                Реестр скопированных файлов: исходный путь -> целевой путь.
        """
        self._copied_files = copied_files

    def convert(
        self,
        link: absLink,
        target_skill_folder: Path,
    ) -> str:
        """Return ``./files/<name>`` for the linked file or directory, copying if needed.

        If the same source path has already been copied, reuse the existing
        target name to avoid duplicates.

        Returns:
            Relative target string such as ``./files/diagram.png`` or
            ``./files/assets``.
        """
        source_path = link.path.os_path
        logger.debug("Converting external file link: %s", source_path)

        if source_path in self._copied_files:
            copied_path = self._copied_files[source_path]
            rel = "./" + copied_path.relative_to(target_skill_folder).as_posix()
            logger.debug("Reusing previously copied external path: %s -> %s", source_path, copied_path)
            return _append_header(rel, link.header)

        files_dir = target_skill_folder / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        original_name = source_path.name
        target_path = files_dir / original_name
        counter = 1
        stem = source_path.stem
        suffix = source_path.suffix
        while target_path.exists():
            target_path = files_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        if source_path.is_dir():
            logger.debug("Copying external directory: %s -> %s", source_path, target_path)
            shutil.copytree(source_path, target_path)
        else:
            logger.debug("Copying external file: %s -> %s", source_path, target_path)
            shutil.copy2(source_path, target_path)
        self._copied_files[source_path] = target_path

        rel = "./" + target_path.relative_to(target_skill_folder).as_posix()
        return _append_header(rel, link.header)


class SourceLinkConverter(absLinkConverter):
    """Converts links that point to files inside another known skill.

    Для ссылок, которые указывают на файлы внутри другого известного скилла.

    Resolution walks the *source* skill list with plain path-containment
    checks - the same checks link validation already performs (see
    ``LinkWithContext.is_link_to_another_skill`` / ``target_skill``) - and
    only translates the result into a final location via ``skill_mapping`` at
    the very end. There is no name-based guessing: a link that validation
    accepted always resolves here the same way, because both use the same
    source-of-truth skill graph.

    Резолюция обходит список *исходных* скиллов простыми проверками на
    вхождение пути - теми же проверками, что уже выполняет валидация ссылок
    (см. ``LinkWithContext.is_link_to_another_skill`` / ``target_skill``) - и
    лишь в самом конце переводит результат в итоговое расположение через
    ``skill_mapping``. Угадывания по имени здесь нет: ссылка, принятая
    валидацией, всегда резолвится здесь так же, потому что обе стороны
    используют один и тот же граф скиллов как источник истины.
    """

    def __init__(self) -> None:
        """Initialize the converter."""
        self._external_converter: Optional[ExternalFileConverter] = None

    @staticmethod
    def _resolve_skill(
        target_path: Path,
        skills: List[Skill],
    ) -> Optional[Tuple["Skill", bool, Optional[Path]]]:
        """Find the source skill that owns ``target_path``.

        Находит исходный скилл, которому принадлежит ``target_path``.

        Returns a triple (skill, is_main_file, rel_path). ``rel_path`` is set
        when the target is a nested file inside the skill's folder.

        Возвращает тройку (skill, is_main_file, rel_path). ``rel_path``
        заполняется, когда цель — вложенный файл внутри папки скилла.
        """
        # EN: Exact match against a skill's main file or folder first.
        # RU: Сначала точное совпадение с основным файлом или папкой скилла.
        for skill in skills:
            if same_path(target_path, skill.file_path):
                return skill, True, None
            if skill.folder_path is not None and same_path(target_path, skill.folder_path):
                return skill, True, None

        # EN: Otherwise, the target may be a file nested inside a skill folder.
        # RU: Иначе цель может быть файлом, вложенным в папку скилла.
        for skill in skills:
            if skill.folder_path is not None and is_relative_to_resolved(target_path, skill.folder_path):
                rel = target_path.relative_to(skill.folder_path)
                return skill, False, rel

        return None

    def convert(
        self,
        link: absLink,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]] = None,
        target_skill_folder: Optional[Path] = None,
        copied_files: Optional[Dict[Path, Path]] = None,
        repo_path: Optional[Path] = None,
        target_dir: Optional[Path] = None,
        **kwargs,
    ) -> str:
        """Resolve a source link against known skills.

        If the target belongs to a known skill, rewrite it as a repo-absolute
        path (e.g. ``skill-b/SKILL.md`` or ``skill-b/docs/extra.md``).
        If the target is not part of any known skill and ``target_skill_folder``
        is provided, copy the file into ``files/`` and return a relative link.

        Если цель принадлежит известному навыку, переписываем ссылку в
        repo-absolute путь (например, ``skill-b/SKILL.md`` или
        ``skill-b/docs/extra.md``).
        Если цель не принадлежит известному навыку и передан
        ``target_skill_folder``, копируем файл в ``files/``.
        """
        target_path = link.path.os_path
        resolved = self._resolve_skill(target_path, skills)

        if resolved is not None:
            skill, is_main_file, rel_path = resolved
            new_skill = (skill_mapping or {}).get(skill, skill)

            # EN: Rewrite the link as a repo-absolute path.
            # RU: Переписываем ссылку в repo-absolute путь.
            effective_repo_path = repo_path if repo_path is not None else _default_repo_path(link)
            target = _finalize_target(new_skill, rel_path, is_main_file, effective_repo_path, target_dir)
            return _append_header(target, link.header)

        # EN: Not part of any known skill: copy to files/ if the adapter
        # provided the target skill folder.
        # RU: Не является частью известного скилла: копируем в files/, если
        # адаптер предоставил целевую папку скилла.
        if target_skill_folder is not None and copied_files is not None:
            self._external_converter = ExternalFileConverter(copied_files)
            return self._external_converter.convert(link, target_skill_folder)

        skill_infos = [
            f"  {s.properties.name}: file={s.file_path.as_posix()}, folder={s.folder_path.as_posix() if s.folder_path else None}"
            for s in skills
        ]
        raise ValueError(
            f"Cannot convert source link {link.raw!r} into skill format: "
            f"no matching skill for {target_path.as_posix()!r}\n"
            f"Known source skills:\n" + "\n".join(skill_infos)
        )


class OsLinkConverter(absLinkConverter):
    """Converts OS-absolute links that live outside the repository.

    Для OS-абсолютных ссылок за пределами репозитория.
    """

    def __init__(self) -> None:
        """Initialize the converter."""
        self._external_converter: Optional[ExternalFileConverter] = None

    def convert(
        self,
        link: absLink,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]] = None,
        target_skill_folder: Optional[Path] = None,
        copied_files: Optional[Dict[Path, Path]] = None,
        **kwargs,
    ) -> str:
        """Copy the linked OS file into ``files/`` and return relative path."""
        if target_skill_folder is None or copied_files is None:
            raise ValueError(
                f"Cannot convert OS link {link.raw!r}: target skill folder is not provided"
            )
        self._external_converter = ExternalFileConverter(copied_files)
        return self._external_converter.convert(link, target_skill_folder)


class LinkConverter:
    """Factory that dispatches links to the right converter by :class:`LinkKind`.

    Фабрика, которая направляет ссылки на нужный конвертер по :class:`LinkKind`.
    """

    def __init__(self) -> None:
        """Initialize converters for every supported link kind."""
        self._converters: Dict[LinkKind, absLinkConverter] = {
            LinkKind.skill: SkillLinkConverter(),
            LinkKind.external: ExternalLinkConverter(),
            LinkKind.source: SourceLinkConverter(),
            LinkKind.os: OsLinkConverter(),
        }

    def convert(
        self,
        link: absLink,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]] = None,
        target_skill_folder: Optional[Path] = None,
        copied_files: Optional[Dict[Path, Path]] = None,
        repo_path: Optional[Path] = None,
        target_dir: Optional[Path] = None,
    ) -> str:
        """Convert ``link`` to the repo-absolute format.

        Args:
            link: Parsed link to convert.
                Распарсенная ссылка для преобразования.
            skills: Known *source* skills used for resolving source links.
                Известные *исходные* навыки, используемые для разрешения source-ссылок.
            skill_mapping: Mapping from original source skill to its current
                location this run.
                / Отображение исходного скилла в его текущее расположение в
                этом запуске.
            target_skill_folder: Folder of the skill currently being adapted.
                Used to copy external files into ``files/``.
                / Папка скилла, который сейчас адаптируется. Используется для
                копирования внешних файлов в ``files/``.
            copied_files: Shared registry of already copied external files.
                / Общий реестр уже скопированных внешних файлов.
            repo_path: Repository root of the sync destination. Falls back to
                the link's own skill's repo path when omitted.
                / Корень репозитория целевого расположения синхронизации. При
                отсутствии используется корень репозитория скилла-владельца
                ссылки.
            target_dir: Root target directory of the current sync. When
                given, repo-absolute targets are built from the skill's name
                and ``target_dir``'s offset from ``repo_path`` alone, so they
                are correct even while the skill's bytes are still sitting in
                a staging directory.
                / Корневая целевая директория текущего синка. При наличии
                repo-absolute цели строятся исключительно из имени скилла и
                смещения ``target_dir`` относительно ``repo_path``, поэтому
                они корректны, даже пока байты скилла всё ещё находятся в
                staging-директории.

        Returns:
            New link target in repo-absolute notation.
                Новая цель ссылки в repo-absolute нотации.

        Raises:
            ValueError: If the link kind is unknown or the source link cannot
                be mapped to a known skill.
        """
        converter = self._converters.get(link.path.kind)
        if converter is None:
            raise ValueError(f"Unknown link kind: {link.path.kind}")
        return converter.convert(
            link,
            skills,
            skill_mapping,
            target_skill_folder=target_skill_folder,
            copied_files=copied_files,
            repo_path=repo_path,
            target_dir=target_dir,
        )
