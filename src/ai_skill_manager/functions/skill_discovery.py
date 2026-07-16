"""Scan configured sources and return the skill candidates found in them.

Сканирование настроенных источников и возврат найденных в них кандидатов
в скиллы.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence, TYPE_CHECKING

from ..models import Result
from ..progress import ProgressCallback
from ..service.skill_discovery.skill_discover import discover

if TYPE_CHECKING:
    from ..entities import Source
    from ..entities.skill_v2 import Skill


class SkillDiscovery:
    """Finds skill candidates in one or more sources - implements step 1.

    Находит кандидатов в скиллы в одном или нескольких источниках -
    реализует шаг 1.

    Reuses the existing source-scanning/pattern-matching/tag-filtering
    machinery (``service.skill_discovery.skill_discover.discover``) unchanged - it
    already builds and returns the new model's ``Skill`` directly, keyed by
    name, collecting a per-candidate error (e.g. a missing/invalid
    frontmatter name, or a name collision) instead of stopping at the first
    one.

    Переиспользует существующий механизм сканирования источников/сопоставления
    по паттернам/фильтрации по тегам (``service.skill_discovery.skill_discover.discover``)
    без изменений - он уже строит и возвращает ``Skill`` новой модели
    напрямую, индексированные по имени, собирая ошибку по каждому кандидату
    (например, отсутствующее/некорректное имя во frontmatter, либо коллизия
    имён) вместо остановки на первой из них.
    """

    def discover(
        self, sources: Sequence["Source"], progress: Optional[ProgressCallback] = None
    ) -> Result[Dict[str, "Skill"]]:
        """Discover skills from ``sources``.

        Обнаруживает скиллы из ``sources``.

        Returns:
            The discovered skills keyed by name, and any per-candidate
            errors. Discovery does not stop at the first error - every
            candidate is attempted.
                / Обнаруженные скиллы, индексированные по имени, и любые
                ошибки по кандидатам. Обнаружение не останавливается на
                первой ошибке - каждый кандидат обрабатывается.
        """
        return discover(sources, progress=progress)
