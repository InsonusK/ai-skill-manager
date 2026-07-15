"""Convert a legacy (file_path/folder_path/format) Skill into the new model.

Преобразование старого (file_path/folder_path/format) Skill в новую модель.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .skill_kind import SkillKind
from .skill_v2 import Skill

if TYPE_CHECKING:
    from .skill import Skill as LegacySkill


def convert_legacy_skill(legacy: "LegacySkill") -> Skill:
    """Build a new-model :class:`Skill` from a legacy-discovery result.

    Reuses the existing pattern-matching discovery strategies (which still
    operate on the legacy shape) without duplicating their logic.

    Строит новый :class:`Skill` из результата обнаружения старой модели.
    Переиспользует существующие стратегии обнаружения по паттернам (которые
    всё ещё работают со старой формой), не дублируя их логику.
    """
    name = legacy.properties.name
    if name is None:
        raise ValueError(f"Skill {legacy.file_path} has no 'name' in frontmatter")

    if legacy.is_flat():
        return Skill(name=name, path=legacy.file_path, kind=SkillKind.flat)

    main_file_relative_path = legacy.file_path.relative_to(legacy.folder_path)
    return Skill(
        name=name,
        path=legacy.folder_path,
        kind=SkillKind.dir,
        main_file_relative_path=main_file_relative_path,
    )
