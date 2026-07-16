"""Default CopySkills implementation: copy files, then rewrite links.

Реализация CopySkills по умолчанию: копирование файлов, затем переписывание
ссылок.
"""

from __future__ import annotations

from pathlib import Path
from typing import AbstractSet, Dict, Optional, TYPE_CHECKING

from .abs_copy_skills import CopySkills
from ..copied_link_rewriter import CopiedLinkRewriter
from ..external_file_copier import ExternalFileCopier
from ..skill_file_copier import SkillFileCopier
from ...progress import ProgressCallback

if TYPE_CHECKING:
    from ...entities.skill_v2 import Skill


class DefaultCopySkills(CopySkills):
    """Plain copy: a skill's own files, then its links rewritten in place.

    Обычное копирование: собственные файлы скилла, затем переписанные на
    месте ссылки.
    """

    def __init__(self) -> None:
        """Initialize the copy/rewrite collaborators."""
        self._skill_file_copier = SkillFileCopier()
        self._external_file_copier = ExternalFileCopier()
        self._link_rewriter = CopiedLinkRewriter(self._external_file_copier)

    def copy(
        self,
        skills: Dict[str, "Skill"],
        target_dir: Path,
        source_repo_path: Path,
        output_repo_path: Path,
        skip_names: AbstractSet[str] = frozenset(),
        progress: Optional[ProgressCallback] = None,
    ) -> Dict[str, Path]:
        """Copy every non-skipped skill's files, then rewrite links across all of them.

        Копирует файлы каждого непропущенного скилла, затем переписывает
        ссылки во всех из них.
        """
        copied_dirs: Dict[str, Path] = {}
        total = len(skills)
        for i, (name, skill) in enumerate(skills.items(), start=1):
            if name in skip_names:
                copied_dirs[name] = target_dir / name
            else:
                copied_dirs[name] = self._skill_file_copier.copy(skill, target_dir)
            if progress is not None:
                progress("copy", i, total)

        for name, skill in skills.items():
            if name in skip_names:
                continue
            self._link_rewriter.rewrite(
                skill,
                copied_dirs[name],
                target_dir,
                skill.repo_path if skill.repo_path is not None else source_repo_path,
                output_repo_path,
                copied_dirs,
                skills,
            )

        return copied_dirs
