"""Scan configured sources and return the skill candidates found in them.

Сканирование настроенных источников и возврат найденных в них кандидатов
в скиллы.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple, TYPE_CHECKING

from ..entities.skill_conversion import convert_legacy_skill
from ..service.discover import discover as legacy_discover

if TYPE_CHECKING:
    from ..entities import Source
    from ..entities.skill_v2 import Skill


class SkillDiscovery:
    """Finds skill candidates in one or more sources - implements step 1.

    Находит кандидатов в скиллы в одном или нескольких источниках -
    реализует шаг 1.

    Reuses the existing source-scanning/pattern-matching/tag-filtering
    machinery (``service.discover.discover``) unchanged, since nested-skill
    detection and per-source-type scanning are not part of what this
    refactor redesigns - only the resulting skills are converted to the new
    model.

    Переиспользует существующий механизм сканирования источников/сопоставления
    по паттернам/фильтрации по тегам (``service.discover.discover``) без
    изменений, поскольку обнаружение вложенных скиллов и сканирование по
    типу источника не входят в то, что редизайнит этот рефакторинг -
    преобразуются в новую модель только итоговые скиллы.
    """

    def discover(self, sources: Sequence["Source"]) -> Tuple[List["Skill"], List[str]]:
        """Discover skills from ``sources``.

        Обнаруживает скиллы из ``sources``.

        Returns:
            The successfully-converted skills and any per-skill conversion
            errors (e.g. a missing/invalid name). Discovery does not stop
            at the first error - every candidate is attempted.
                / Успешно преобразованные скиллы и ошибки преобразования по
                каждому скиллу (например, отсутствующее/некорректное имя).
                Обнаружение не останавливается на первой ошибке - каждый
                кандидат обрабатывается.
        """
        legacy_skills = legacy_discover(sources)

        skills: List["Skill"] = []
        errors: List[str] = []
        for legacy in legacy_skills:
            try:
                skills.append(convert_legacy_skill(legacy))
            except ValueError as exc:
                errors.append(str(exc))

        return skills, errors
