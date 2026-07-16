"""CopySkills decorator that removes previously-synced skills no longer present.

Декоратор CopySkills, удаляющий ранее синхронизированные скиллы, которых
больше нет.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import AbstractSet, Dict, Optional, TYPE_CHECKING

from .abs_copy_skills import CopySkills
from ..managed_state import is_managed
from ...progress import ProgressCallback

if TYPE_CHECKING:
    from ...entities.skill_v2 import Skill


class OrphanRemovingCopySkills(CopySkills):
    """Deletes managed target directories not among this run's copied skills.

    Удаляет управляемые целевые директории, не входящие в скиллы,
    скопированные в этом запуске.

    Only directories tagged as managed by this tool are ever removed - a
    hand-written directory living next to synced skills is left alone.

    Удаляются только директории, помеченные этим инструментом как
    управляемые - написанная вручную директория рядом с синхронизированными
    скиллами не трогается.
    """

    def __init__(self, wrapped: CopySkills) -> None:
        """Initialize with the ``CopySkills`` to run before removing orphans."""
        self._wrapped = wrapped

    def copy(
        self,
        skills: Dict[str, "Skill"],
        target_dir: Path,
        source_repo_path: Path,
        output_repo_path: Path,
        skip_names: AbstractSet[str] = frozenset(),
        progress: Optional[ProgressCallback] = None,
    ) -> Dict[str, Path]:
        """Copy via the wrapped implementation, then remove orphaned directories."""
        copied_dirs = self._wrapped.copy(
            skills, target_dir, source_repo_path, output_repo_path, skip_names, progress=progress
        )

        if target_dir.is_dir():
            current_dirs = {path.resolve() for path in copied_dirs.values()}
            for entry in target_dir.iterdir():
                if entry.is_dir() and is_managed(entry) and entry.resolve() not in current_dirs:
                    shutil.rmtree(entry)

        return copied_dirs
