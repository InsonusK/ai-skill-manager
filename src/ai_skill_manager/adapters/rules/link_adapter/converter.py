"""Link converters for the agent skill-link format.

Конвертеры ссылок в формат агентских skill-link.
"""

from __future__ import annotations

import logging
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from ....entities import LinkKind, absLink

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
    ) -> str:
        """Convert a link to the agent skill-link format.

        Преобразует ссылку в формат агентской skill-link.

        Args:
            link: The parsed link to convert.
                Распарсенная ссылка для преобразования.
            skills: All known skills for resolving cross-skill links.
                Все известные навыки для разрешения меж-скилловых ссылок.
            skill_mapping: Optional mapping from original source skill to copied
                target skill. Used to resolve source links that still point to
                the original source paths after copying.
                / Опциональное отображение исходного скилла в скопированный.
                Используется для разрешения source-ссылок, которые после
                копирования всё ещё указывают на исходные пути.

        Returns:
            The new link target string.
                Новая строка цели ссылки.
        """
        ...


class SkillLinkConverter(absLinkConverter):
    """Converts links that point inside the current skill.

    Для ссылок, которые указывают внутрь текущего скилла.
    """

    def convert(
        self,
        link: absLink,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]] = None,
        **kwargs,
    ) -> str:
        """Return the repo-absolute path to the target, preserving any header."""
        # EN: Internal skill links are rewritten to repo-absolute paths.
        # RU: Внутренние ссылки скилла переписываются в repo-absolute пути.
        repo_path = link.skill_file.skill.source.get_scan_location().repo_path
        target = _repo_absolute_path(link.path.os_path, repo_path)
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
    """

    def __init__(self) -> None:
        """Initialize the converter."""
        self._external_converter: Optional[ExternalFileConverter] = None
        self._norm_cache: dict[Path, Path] = {}
        self._resolve_indexes: Optional[dict] = None
        self._resolve_indexes_key: Optional[tuple] = None

    def _build_resolve_indexes(
        self,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]],
    ) -> dict:
        """Build lookup tables for fast skill resolution.

        The original implementation compared the link target against every
        known skill path for every link. These indexes turn the same lookup
        into a handful of dictionary accesses and a short parent walk.
        """
        _norm = self._norm

        target_file_to_skill: dict[Path, "Skill"] = {}
        target_folder_to_skill: dict[Path, "Skill"] = {}
        for skill in skills:
            target_file_to_skill[_norm(skill.file_path)] = skill
            if skill.folder_path is not None:
                target_folder_to_skill[_norm(skill.folder_path)] = skill

        old_file_to_new: dict[Path, Tuple["Skill", bool, Optional[Path]]] = {}
        old_folder_full: dict[Path, Tuple["Skill", Path]] = {}
        old_folder_name: dict[str, List[Tuple["Skill", Path]]] = {}
        old_identities: List[Tuple[Path, Tuple[str, ...], "Skill", Path]] = []
        old_flat_identities: List[Tuple[Path, Tuple[str, ...], "Skill"]] = []
        old_file_names: dict[str, List[Tuple["Skill", bool, Optional[Path]]]] = {}
        old_stem_names: dict[str, List[Tuple["Skill", bool, Optional[Path]]]] = {}

        norm_source_path: Optional[Path] = None
        if skill_mapping:
            if skills:
                norm_source_path = _norm(skills[0].source_path)

            for old_skill, new_skill in skill_mapping.items():
                norm_old_file = _norm(old_skill.file_path)
                old_file_to_new[norm_old_file] = (new_skill, True, None)

                if old_skill.folder_path is not None:
                    norm_old_folder = _norm(old_skill.folder_path)
                    old_main_rel = old_skill.file_path.relative_to(old_skill.folder_path)

                    # Exact old folder -> main file link.
                    old_folder_full[norm_old_folder] = (new_skill, old_main_rel)

                    # Name-based match for skills moved to a different root.
                    old_folder_name.setdefault(norm_old_folder.name, []).append(
                        (new_skill, old_main_rel)
                    )

                    norm_old_source_path = _norm(old_skill.source_path)
                    old_identity = norm_old_folder.relative_to(norm_old_source_path)
                    old_identities.append(
                        (old_identity, tuple(old_identity.parts), new_skill, old_main_rel)
                    )
                else:
                    norm_old_source_path = _norm(old_skill.source_path)
                    old_identity = norm_old_file.relative_to(norm_old_source_path)
                    old_flat_identities.append(
                        (old_identity, tuple(old_identity.parts), new_skill)
                    )

                    old_file_names.setdefault(old_skill.file_path.name, []).append(
                        (new_skill, True, None)
                    )
                    old_stem_names.setdefault(old_skill.file_path.stem, []).append(
                        (new_skill, True, None)
                    )

        return {
            "norm_source_path": norm_source_path,
            "target_file_to_skill": target_file_to_skill,
            "target_folder_to_skill": target_folder_to_skill,
            "old_file_to_new": old_file_to_new,
            "old_folder_full": old_folder_full,
            "old_folder_name": old_folder_name,
            "old_identities": old_identities,
            "old_flat_identities": old_flat_identities,
            "old_file_names": old_file_names,
            "old_stem_names": old_stem_names,
        }

    def _resolve_skill(
        self,
        target_path: Path,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]],
    ) -> Optional[Tuple["Skill", bool, Optional[Path]]]:
        """Find the copied skill that owns ``target_path``.

        Возвращает тройку (skill, is_main_file, rel_path). ``rel_path``
        заполняется, когда цель найдена по старому имени папки/файла, и
        указывает путь внутри скопированного скилла.
        """
        norm_target = self._norm(target_path)

        cache_key = (id(skills), id(skill_mapping))
        if cache_key != self._resolve_indexes_key:
            self._resolve_indexes = self._build_resolve_indexes(skills, skill_mapping)
            self._resolve_indexes_key = cache_key
        idx = self._resolve_indexes
        assert idx is not None

        # EN: Exact match against copied target skills first.
        # RU: Сначала точное совпадение со скопированными навыками.
        skill = idx["target_file_to_skill"].get(norm_target)
        if skill is not None:
            return skill, True, None
        skill = idx["target_folder_to_skill"].get(norm_target)
        if skill is not None:
            return skill, True, None

        if skill_mapping:
            # EN: Exact match against original source skill paths.
            result = idx["old_file_to_new"].get(norm_target)
            if result is not None:
                return result

            # EN: Target is inside an original source skill folder.
            for parent in norm_target.parents:
                entry = idx["old_folder_full"].get(parent)
                if entry is not None:
                    new_skill, old_main_rel = entry
                    rel_path = norm_target.relative_to(parent)
                    is_main = rel_path == Path(".") or rel_path == old_main_rel
                    return new_skill, is_main, None if is_main else rel_path

            # EN: Match by the relative identity of the original skill inside
            # the repository (repo-absolute links with preserved structure).
            norm_source_path = idx["norm_source_path"]
            if norm_source_path is not None and norm_target.is_relative_to(norm_source_path):
                target_rel = norm_target.relative_to(norm_source_path)
                target_rel_parts = target_rel.parts

                for old_identity, old_identity_parts, new_skill, old_main_rel in idx["old_identities"]:
                    n = len(old_identity_parts)
                    if len(target_rel_parts) >= n and target_rel_parts[-n:] == old_identity_parts:
                        rel_path = target_rel.relative_to(old_identity)
                        is_main = rel_path == Path(".") or rel_path == old_main_rel
                        return new_skill, is_main, None if is_main else rel_path

                for old_identity, old_identity_parts, new_skill in idx["old_flat_identities"]:
                    n = len(old_identity_parts)
                    if len(target_rel_parts) >= n and target_rel_parts[-n:] == old_identity_parts:
                        return new_skill, True, None

            # EN: Skill moved to a different root directory -- match by folder
            # or file name while walking up the target path.
            for parent in norm_target.parents:
                entries = idx["old_folder_name"].get(parent.name)
                if entries:
                    for new_skill, old_main_rel in entries:
                        rel_path = norm_target.relative_to(parent)
                        is_main = rel_path == Path(".") or rel_path == old_main_rel
                        return new_skill, is_main, None if is_main else rel_path

            # EN: Flat skill fallback by file name or stem.
            entries = idx["old_file_names"].get(norm_target.name)
            if entries:
                return entries[0]
            entries = idx["old_stem_names"].get(norm_target.name)
            if entries:
                return entries[0]

        # EN: Last resort: the target is somewhere inside a copied skill folder.
        for parent in norm_target.parents:
            skill = idx["target_folder_to_skill"].get(parent)
            if skill is not None:
                return skill, False, None

        return None

    @property
    def _norm(self):
        """Return a cached path normaliser."""
        cache = self._norm_cache

        def _norm_path(path: Path) -> Path:
            cached = cache.get(path)
            if cached is not None:
                return cached
            if path.exists():
                result = path.resolve()
            else:
                result = path
            cache[path] = result
            return result

        return _norm_path

    def convert(
        self,
        link: absLink,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]] = None,
        target_skill_folder: Optional[Path] = None,
        copied_files: Optional[Dict[Path, Path]] = None,
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
        resolved = self._resolve_skill(target_path, skills, skill_mapping)

        if resolved is not None:
            skill, is_main_file, rel_path_override = resolved

            # EN: Determine the absolute target path inside the resolved skill.
            # RU: Определяем абсолютный путь цели внутри разрешённого скилла.
            if is_main_file or target_path == skill.file_path:
                final_path = skill.file_path
            else:
                folder = skill.folder_path
                assert folder is not None, "skill with nested file must have a folder"
                if rel_path_override is not None:
                    final_path = folder / rel_path_override
                else:
                    final_path = target_path

            # EN: Rewrite the link as a repo-absolute path.
            # RU: Переписываем ссылку в repo-absolute путь.
            repo_path = link.skill_file.skill.source.get_scan_location().repo_path
            target = _repo_absolute_path(final_path, repo_path)
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
        mapping_infos = []
        if skill_mapping:
            for old, new in skill_mapping.items():
                mapping_infos.append(
                    f"  old({old.format.value}) name={old.properties.name} "
                    f"file={old.file_path.as_posix()} "
                    f"folder={old.folder_path.as_posix() if old.folder_path else None} "
                    f"-> new({new.format.value}) name={new.properties.name} "
                    f"file={new.file_path.as_posix()} "
                    f"folder={new.folder_path.as_posix() if new.folder_path else None}"
                )
        raise ValueError(
            f"Cannot convert source link {link.raw!r} into skill format: "
            f"no matching skill for {target_path.as_posix()!r}\n"
            f"Known target skills:\n" + "\n".join(skill_infos) + "\n"
            f"Source-to-target mapping:\n" + "\n".join(mapping_infos)
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
    ) -> str:
        """Convert ``link`` to the repo-absolute format.

        Args:
            link: Parsed link to convert.
                Распарсенная ссылка для преобразования.
            skills: Known skills used for resolving source links.
                Известные навыки, используемые для разрешения source-ссылок.
            skill_mapping: Optional mapping from original source skill to copied
                target skill.
                / Опциональное отображение исходного скилла в скопированный.
            target_skill_folder: Folder of the skill currently being adapted.
                Used to copy external files into ``files/``.
                / Папка скилла, который сейчас адаптируется. Используется для
                копирования внешних файлов в ``files/``.
            copied_files: Shared registry of already copied external files.
                / Общий реестр уже скопированных внешних файлов.

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
        )
