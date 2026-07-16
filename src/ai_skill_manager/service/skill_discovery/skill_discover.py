"""Discovery service.

High-level helper that resolves each configured source to its scan
locations and returns the combined name-keyed skill dict.

Сервис обнаружения.
Высокоуровневый помощник, который разрешает каждый настроенный источник
в его локации сканирования и возвращает объединённый словарь навыков,
индексированный по имени.
"""

import logging
from typing import Dict, List, Optional, Sequence

from .skill import AutoDiscovery
from ...entities import Source
from ...entities.skill_v2 import Skill
from ...functions.skill_dict_builder import SkillDictBuilder
from ...models import Result
from ...progress import ProgressCallback
from ...functions.tag_filter import filter_skills_by_tags

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


def discover(
    sources: Sequence[Source],
    progress: Optional[ProgressCallback] = None,
) -> Result[Dict[str, Skill]]:
    """Discover skills from a list of sources.

    Discover skills from a list of sources.

    Обнаружить навыки из списка источников.

    Args:
        sources: Skill sources to scan. Expected to already be fully formed
            (e.g. built by :class:`SourceFactory`), with any local paths
            already resolved to absolute form. /
            Источники навыков для сканирования. Ожидаются уже полностью
            сформированными (например, построенными :class:`SourceFactory`),
            с локальными путями, уже разрешёнными в абсолютную форму.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        The discovered skills keyed by name, and any per-candidate errors
        (e.g. a missing frontmatter name, or two different skills sharing a
        name) collected while scanning. Structural conflicts (e.g. ambiguous
        pattern matches) still raise. /
        Обнаруженные скиллы, индексированные по имени, и любые ошибки по
        кандидатам (например, отсутствующее имя во frontmatter, либо два
        разных скилла с одинаковым именем), собранные при сканировании.
        Структурные конфликты (например, неоднозначные совпадения паттернов)
        по-прежнему вызывают исключение.

    Raises:
        ValueError: If an unknown source type is encountered, or a structural
            skill definition conflict is found.
        ValueError: Если встречен неизвестный тип источника, либо найден
            структурный конфликт определения скилла.
    """
    all_skills: List[Skill] = []
    all_errors: List[str] = []
    sources = list(sources)

    logger.debug("Discovering skills from %d source(s)", len(sources))

    if progress is not None:
        progress("discover", 0, len(sources))

    for index, src in enumerate(sources, start=1):
        scan_locations = src.get_scan_locations()
        logger.debug(
            "Source %d/%d: %s (type=%s, %d scan location(s))",
            index,
            len(sources),
            src,
            src.source_type,
            len(scan_locations),
        )

        source_skills: List[Skill] = []
        source_errors: List[str] = []
        for scan_location in scan_locations:
            logger.debug(
                "Resolved scan location: repo_path=%s scan_path=%s",
                scan_location.repo_path,
                scan_location.scan_path,
            )
            strategy = AutoDiscovery(
                source_path=scan_location.scan_path,
                source=src,
            )
            location_skills, location_errors = strategy.discover()
            for skill in location_skills:
                skill.repo_path = scan_location.repo_path
            source_skills.extend(location_skills)
            source_errors.extend(location_errors)

        logger.debug(
            "Source %d/%d discovered %d skill(s)",
            index,
            len(sources),
            len(source_skills),
        )

        if src.tags:
            source_skills = filter_skills_by_tags(source_skills, src.tags)
            logger.debug(
                "Source %d/%d retained %d skill(s) after tag filter",
                index,
                len(sources),
                len(source_skills),
            )

        all_skills.extend(source_skills)
        all_errors.extend(source_errors)
        if progress is not None:
            progress("discover", index, len(sources))

    # EN: Index by name, collecting an error for each name collision instead
    # of a plain list with duplicates from overlapping sources.
    # RU: Индексируем по имени, собирая ошибку при каждой коллизии имён вместо
    # простого списка с дубликатами из пересекающихся источников.
    skills_by_name, collision_errors = SkillDictBuilder().build(all_skills)
    all_errors.extend(collision_errors)

    return Result(skills_by_name, all_errors)
