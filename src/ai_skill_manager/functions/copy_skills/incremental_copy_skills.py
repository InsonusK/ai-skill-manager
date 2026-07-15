"""CopySkills decorator that skips re-copying an unchanged skill.

Декоратор CopySkills, пропускающий повторное копирование неизменившегося
скилла.
"""

from __future__ import annotations

from pathlib import Path
from typing import AbstractSet, Dict, Set, TYPE_CHECKING

from .abs_copy_skills import CopySkills
from ..managed_state import is_managed, read_managed_state, write_managed_state
from ..skill_hash import compute_skill_hash

if TYPE_CHECKING:
    from ...entities.skill_v2 import Skill


class IncrementalCopySkills(CopySkills):
    """Skips re-materializing a skill whose source hash and version match.

    Пропускает повторную материализацию скилла, чей исходный хеш и версия
    совпадают.

    A skill is up to date when its target directory was created by this
    tool, and the stored hash/version in its managed-state marker match the
    current source hash and ``version``. ``version`` should change whenever
    the wrapped ``CopySkills`` chain's behavior changes, so a stale copy is
    never kept just because its content hash happens to match.

    Скилл считается актуальным, если его целевая директория была создана
    этим инструментом, а хеш/версия, сохранённые в маркере managed-state,
    совпадают с текущим исходным хешем и ``version``. ``version`` должна
    меняться при изменении поведения обёрнутой цепочки ``CopySkills``,
    чтобы устаревшая копия никогда не сохранялась только потому, что её
    хеш содержимого случайно совпал.
    """

    def __init__(self, wrapped: CopySkills, version: str, force: bool = False) -> None:
        """Initialize with the wrapped copier, a cache-busting version, and force."""
        self._wrapped = wrapped
        self._version = version
        self._force = force

    def copy(
        self,
        skills: Dict[str, "Skill"],
        target_dir: Path,
        source_repo_path: Path,
        output_repo_path: Path,
        skip_names: AbstractSet[str] = frozenset(),
    ) -> Dict[str, Path]:
        """Copy only the skills that are missing or out of date."""
        up_to_date: Set[str] = set(skip_names)
        for name, skill in skills.items():
            if name in up_to_date:
                continue
            if not self._force and self._is_up_to_date(skill, target_dir / name):
                up_to_date.add(name)

        copied_dirs = self._wrapped.copy(skills, target_dir, source_repo_path, output_repo_path, up_to_date)

        for name, skill in skills.items():
            if name in skip_names or name in (up_to_date - set(skip_names)):
                continue
            write_managed_state(copied_dirs[name], {"hash": compute_skill_hash(skill), "version": self._version})

        return copied_dirs

    def _is_up_to_date(self, skill: "Skill", existing_dir: Path) -> bool:
        """Return whether ``existing_dir`` already holds the current copy of ``skill``."""
        if not existing_dir.is_dir() or not (existing_dir / "SKILL.md").is_file():
            return False
        if not is_managed(existing_dir):
            return False
        state = read_managed_state(existing_dir)
        if state is None:
            return False
        return state.get("hash") == compute_skill_hash(skill) and state.get("version") == self._version
