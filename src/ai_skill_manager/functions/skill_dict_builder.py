"""Insert discovered skills into the name-keyed skill dict.

Вставка обнаруженных скиллов в словарь скиллов, индексированный по имени.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.skill_v2 import Skill


class SkillDictBuilder:
    """Builds/extends the ``name -> Skill`` dict, erroring on name collisions.

    Строит/расширяет словарь ``имя -> Skill``, сообщая об ошибке при
    коллизии имён.
    """

    def build(
        self,
        skills: Iterable["Skill"],
        existing: Optional[Dict[str, "Skill"]] = None,
    ) -> Tuple[Dict[str, "Skill"], List[str]]:
        """Insert ``skills`` into ``existing`` (or a new dict) by name.

        Вставляет ``skills`` в ``existing`` (или новый словарь) по имени.

        Returns:
            The resulting dict and a list of collision error messages. A
            skill whose name collides with a *different* already-present
            skill is not inserted and produces an error; re-adding the
            exact same skill is a silent no-op.
                / Итоговый словарь и список сообщений об ошибках коллизий.
                Скилл, чьё имя сталкивается с *другим* уже присутствующим
                скиллом, не вставляется и порождает ошибку; повторное
                добавление того же самого скилла - тихий no-op.
        """
        result = dict(existing) if existing else {}
        errors: List[str] = []

        for skill in skills:
            current = result.get(skill.name)
            if current is None:
                result[skill.name] = skill
                continue
            if current == skill:
                continue
            errors.append(
                f"Duplicate skill name {skill.name!r}: found at both "
                f"{current.path} and {skill.path}"
            )

        return result, errors
