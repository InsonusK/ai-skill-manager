"""Link converters for the agent skill-link format.

Конвертеры ссылок в формат агентских skill-link.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from ....entities import LinkKind, absLink

if TYPE_CHECKING:
    from ....entities import Skill


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
        """Return the already-relative skill path, preserving any header."""
        # EN: Links inside the same skill keep their relative path.
        # RU: Ссылки внутри того же скилла сохраняют свой относительный путь.
        return _append_header(link.path.formatted, link.header)


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
    """Copies a non-skill file into ``files/`` and returns the relative link.

    Копирует файл, не принадлежащий скиллу, в ``files/`` и возвращает
    относительную ссылку.
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
        """Return ``./files/<name>`` for the linked file, copying if needed.

        If the same source file has already been copied, reuse the existing
        target name to avoid duplicates.

        Returns:
            Relative target string such as ``./files/diagram.png``.
        """
        source_path = link.path.os_path
        if source_path in self._copied_files:
            copied_path = self._copied_files[source_path]
            rel = "./" + copied_path.relative_to(target_skill_folder).as_posix()
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

        import shutil
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

        Сначала ищем точное совпадение среди скопированных навыков, затем
        ищем исходный навык через ``skill_mapping`` (он точнее знает, является
        ли цель основным файлом), и только потом соглашаемся на любое
        вхождение в папку скопированного навыка.
        """
        # EN: Normalise paths so comparisons are not affected by symlinks or
        # redundant separators. Resolve only when the path exists to avoid
        # raising for links that still point to the original source tree.
        # RU: Нормализуем пути, чтобы сравнения не зависели от symlink или
        # лишних разделителей. Resolve вызываем только для существующих путей,
        # чтобы не падать на ссылках, которые всё ещё указывают на исходное
        # дерево.
        def _norm(path: Path) -> Path:
            if path.exists():
                return path.resolve()
            return path

        norm_target = _norm(target_path)

        # EN: Exact match against copied target skills first. A link pointing
        # to the skill folder itself is treated as a link to the skill's main
        # file (e.g. a repo-absolute path without the ``.md`` extension).
        # RU: Сначала точное совпадение со скопированными навыками. Ссылка,
        # указывающая на папку скилла, считается ссылкой на основной файл
        # (например, repo-absolute путь без суффикса ``.md``).
        for skill in skills:
            norm_file = _norm(skill.file_path)
            if norm_target == norm_file:
                return skill, True, None
            if skill.folder_path is not None:
                norm_folder = _norm(skill.folder_path)
                if norm_target == norm_folder:
                    return skill, True, None

        # EN: Fallback using the source-to-target mapping. This is more precise
        # because it knows the original skill layout and can detect links to
        # the old main file name even after it was renamed to ``SKILL.md``.
        # RU: Fallback через маппинг исходных скиллов в целевые. Это точнее,
        # потому что знает исходную структуру и может распознать ссылку на
        # старое имя основного файла даже после переименования в ``SKILL.md``.
        if skill_mapping:
            source_path = skills[0].source_path if skills else None
            norm_source_path = _norm(source_path) if source_path else None
            target_rel = (
                norm_target.relative_to(norm_source_path)
                if norm_source_path and norm_target.is_relative_to(norm_source_path)
                else None
            )

            for old_skill, new_skill in skill_mapping.items():
                norm_old_file = _norm(old_skill.file_path)
                norm_old_folder = _norm(old_skill.folder_path) if old_skill.folder_path else None

                # EN: Exact path match against the original source skill. A
                # link pointing to the original skill folder is also a main-file
                # link (common for repo-absolute paths without the ``.md`` suffix).
                # RU: Точное совпадение с исходным скиллом. Ссылка, указывающая
                # на исходную папку скилла, тоже считается ссылкой на основной
                # файл (типично для repo-absolute путей без суффикса ``.md``).
                if norm_target == norm_old_file or norm_target == norm_old_folder:
                    return new_skill, True, None

                if norm_old_folder is not None and norm_target.is_relative_to(norm_old_folder):
                    rel_path = norm_target.relative_to(norm_old_folder)
                    old_main_rel = old_skill.file_path.relative_to(old_skill.folder_path)
                    is_main = rel_path == Path(".") or rel_path == old_main_rel
                    return new_skill, is_main, None if is_main else rel_path

                # EN: Match by the relative identity of the original skill inside
                # the repository. This handles repo-absolute links where the
                # target tree keeps the same nested structure as the source tree.
                # RU: Сопоставление по относительному пути исходного скилла в
                # репозитории. Покрывает repo-absolute ссылки, где target-дерево
                # сохраняет ту же вложенную струстуру, что и source.
                norm_old_source_path = _norm(old_skill.source_path)
                if old_skill.folder_path is not None:
                    old_identity = norm_old_folder.relative_to(norm_old_source_path)
                else:
                    old_identity = norm_old_file.relative_to(norm_old_source_path)

                if target_rel is not None and len(target_rel.parts) >= len(old_identity.parts):
                    if target_rel.parts[-len(old_identity.parts):] == old_identity.parts:
                        if old_skill.folder_path is not None:
                            rel_path = target_rel.relative_to(old_identity)
                            is_main = (
                                rel_path == Path(".")
                                or rel_path == old_skill.file_path.relative_to(old_skill.folder_path)
                            )
                            return new_skill, is_main, None if is_main else rel_path
                        else:
                            return new_skill, True, None

                # EN: The link may point directly to the original skill folder
                # by name (repo-absolute paths without ``.md`` often resolve to
                # the folder itself).
                # RU: Ссылка может указывать прямо на исходную папку скилла по
                # имени (repo-absolute пути без ``.md`` часто разрешаются в саму
                # папку).
                if norm_old_folder is not None and norm_target.name == norm_old_folder.name:
                    return new_skill, True, None

                # EN: The copied target tree may still use the old source folder
                # or file names. Walk up the target path and look for the old
                # skill's folder/file name. This handles cases where the skill
                # was moved to a different root directory during sync.
                # RU: Скопированное дерево может всё ещё использовать старые
                # имена папок/файлов. Идём вверх по target_path и ищем имя
                # старой папки/файла скилла. Это покрывает случаи, когда скилл
                # был перемещён в другой корневой каталог при синхронизации.
                if norm_old_folder is not None:
                    old_folder_name = norm_old_folder.name
                    for parent in norm_target.parents:
                        if parent.name == old_folder_name:
                            rel_path = norm_target.relative_to(parent)
                            old_main_rel = old_skill.file_path.relative_to(old_skill.folder_path)
                            is_main = rel_path == Path(".") or rel_path == old_main_rel
                            return new_skill, is_main, None if is_main else rel_path
                else:
                    if norm_target.name == old_skill.file_path.name:
                        return new_skill, True, None
                    # EN: A repo-absolute link may resolve to the folder that
                    # shares its name with a flat skill's file stem (without
                    # the ``.md`` suffix).
                    # RU: Repo-absolute ссылка может разрешиться в папку,
                    # имя которой совпадает с stem имени файла плоского скилла
                    # (без суффикса ``.md``).
                    if norm_target.name == old_skill.file_path.stem:
                        return new_skill, True, None

        # EN: Last resort: the target is somewhere inside a copied skill folder.
        # RU: Последняя инстанция: цель где-то внутри папки скопированного скилла.
        for skill in skills:
            if skill.folder_path is not None:
                norm_folder = _norm(skill.folder_path)
                if norm_target.is_relative_to(norm_folder):
                    return skill, False, None

        return None

    def convert(
        self,
        link: absLink,
        skills: List[Skill],
        skill_mapping: Optional[Dict[Skill, Skill]] = None,
        target_skill_folder: Optional[Path] = None,
        copied_files: Optional[Dict[Path, Path]] = None,
    ) -> str:
        """Resolve a source link against known skills.

        Если цель совпадает с основным файлом навыка — используем ``skill:<name>``.
        Если цель находится внутри папки навыка — добавляем ``;file:<relative>``.
        Если цель не принадлежит известному навыку и передан ``target_skill_folder``,
        копируем файл в ``files/``.
        """
        target_path = link.path.os_path
        resolved = self._resolve_skill(target_path, skills, skill_mapping)

        if resolved is not None:
            skill, is_main_file, rel_path_override = resolved
            skill_name = skill.properties.name
            if skill_name is None:
                raise ValueError(
                    f"Cannot convert source link {link.raw!r} into skill format: "
                    f"skill {skill.file_path.as_posix()!r} has no name"
                )

            # EN: Link points directly to the skill's main file.
            # RU: Ссылка ведёт прямо на основной файл скилла.
            if is_main_file or target_path == skill.file_path:
                return _append_header(f"skill:{skill_name}", link.header)

            # EN: The target path points inside the skill folder.
            # RU: Цель указывает внутрь папки скилла.
            if rel_path_override is not None:
                rel_path = rel_path_override.as_posix()
            else:
                folder = skill.folder_path
                assert folder is not None, "skill with nested file must have a folder"
                rel_path = target_path.relative_to(folder).as_posix()
            return _append_header(
                f"skill:{skill_name};file:./{rel_path}",
                link.header,
            )

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
        """Convert ``link`` to the agent skill-link format.

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
            New link target in agent skill-link notation.
                Новая цель ссылки в нотации агентской skill-link.

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
