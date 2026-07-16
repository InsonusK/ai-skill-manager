"""Rewrite a copied file's links to point at their targets' copied locations.

Переписывание ссылок скопированного файла так, чтобы они указывали на
скопированные расположения своих целей.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING, Tuple

from ..entities.link.link_target import ExternalLinkTarget, SkillLinkTarget
from ..entities.skill_file_v2 import MarkdownSkillFile

if TYPE_CHECKING:
    from ..entities.link.file_link import FileLink
    from ..entities.skill_v2 import Skill
    from .external_file_copier import ExternalFileCopier

# Placeholder substituted when a link's target skill/copy is unexpectedly
# missing (should not happen once discovery succeeded with zero errors, but
# guards against surprises rather than crashing the whole copy).
# Заглушка, подставляемая, когда целевой скилл/копия ссылки неожиданно
# отсутствует (не должно происходить, если обнаружение прошло без ошибок,
# но защищает от неожиданностей вместо падения всего копирования).
BROKEN_LINK_PLACEHOLDER = "#unresolved-link"


class CopiedLinkRewriter:
    """Rewrites links in one already-copied skill's files - step 3, pass 2.

    Переписывает ссылки в файлах уже скопированного скилла - шаг 3, проход 2.

    Two different repository roots are involved and must not be confused:
    ``source_repo_path`` is where an :class:`ExternalLinkTarget`'s file
    physically lives (needed to *copy* it), while ``output_repo_path`` is
    the root the rewritten link text is expressed relative to (needed to
    *format* it) - these are unrelated in general (e.g. when syncing from a
    GitHub source into a local target).

    Задействованы два разных корня репозитория, которые нельзя путать:
    ``source_repo_path`` - место, где физически находится файл
    :class:`ExternalLinkTarget` (нужен, чтобы его *скопировать*), а
    ``output_repo_path`` - корень, относительно которого формируется текст
    переписанной ссылки (нужен, чтобы её *отформатировать*) - в общем
    случае они никак не связаны (например, при синхронизации из источника
    GitHub в локальный target).
    """

    def __init__(self, external_file_copier: "ExternalFileCopier") -> None:
        """Initialize with the collaborator used to materialize external files."""
        self._external_file_copier = external_file_copier

    def rewrite(
        self,
        skill: "Skill",
        skill_target_dir: Path,
        target_dir: Path,
        source_repo_path: Path,
        output_repo_path: Path,
        copied_skill_dirs: Dict[str, Path],
        known_skills: Dict[str, "Skill"],
    ) -> int:
        """Rewrite every link in ``skill``'s copied markdown files.

        Переписывает каждую ссылку в скопированных markdown-файлах ``skill``.

        Returns:
            The number of links rewritten. / Количество переписанных ссылок.
        """
        total = 0
        for skill_file in skill.files:
            if not isinstance(skill_file, MarkdownSkillFile) or not skill_file.links:
                continue

            destination = (
                skill_target_dir / "SKILL.md"
                if skill.is_main_file(skill_file.path)
                else skill_target_dir / skill_file.path
            )
            content = destination.read_text(encoding="utf-8")
            new_content, count = self._replace_links(
                content, skill_file.links, target_dir, source_repo_path, output_repo_path,
                copied_skill_dirs, known_skills,
            )
            if count:
                destination.write_text(new_content, encoding="utf-8")
            total += count

        return total

    def _replace_links(
        self,
        content: str,
        links: List["FileLink"],
        target_dir: Path,
        source_repo_path: Path,
        output_repo_path: Path,
        copied_skill_dirs: Dict[str, Path],
        known_skills: Dict[str, "Skill"],
    ) -> Tuple[str, int]:
        """Replace every link's raw text with its resolved copied-target string."""
        sorted_links = sorted(links, key=lambda link: link.start, reverse=True)

        fragments: List[str] = []
        last_start = len(content)
        replaced = 0

        for link in sorted_links:
            new_target = self._resolve_copied_target(
                link, target_dir, source_repo_path, output_repo_path, copied_skill_dirs, known_skills,
            )
            prefix = "!" if link.is_image else ""
            new_raw = f"{prefix}[{link.text}]({new_target})"

            fragments.append(content[link.end : last_start])
            fragments.append(new_raw)
            last_start = link.start
            replaced += 1

        fragments.append(content[:last_start])
        fragments.reverse()
        return "".join(fragments), replaced

    def _resolve_copied_target(
        self,
        link: "FileLink",
        target_dir: Path,
        source_repo_path: Path,
        output_repo_path: Path,
        copied_skill_dirs: Dict[str, Path],
        known_skills: Dict[str, "Skill"],
    ) -> str:
        """Compute the repo-absolute string a link should be rewritten to."""
        target = link.target

        if isinstance(target, SkillLinkTarget):
            copied_dir = copied_skill_dirs.get(target.skill_name)
            target_skill = known_skills.get(target.skill_name)
            if copied_dir is None or target_skill is None:
                result = BROKEN_LINK_PLACEHOLDER
            else:
                final_path = (
                    copied_dir / "SKILL.md"
                    if target_skill.is_main_file(target.relative_path)
                    else copied_dir / target.relative_path
                )
                result = Path(os.path.relpath(final_path, output_repo_path)).as_posix()
        elif isinstance(target, ExternalLinkTarget):
            copied_relative = self._external_file_copier.copy(target.repo_absolute_path, source_repo_path, target_dir)
            result = Path(os.path.relpath(target_dir / copied_relative, output_repo_path)).as_posix()
        else:
            result = BROKEN_LINK_PLACEHOLDER

        return f"{result}{link.header}" if link.header else result
