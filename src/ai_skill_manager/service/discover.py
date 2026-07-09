"""Discovery service.

High-level helper that resolves each configured source to its scan location
and returns the combined list of skills.

Сервис обнаружения.
Высокоуровневый помощник, который разрешает каждый настроенный источник
в его локацию сканирования и возвращает объединённый список навыков.
"""

import logging
from pathlib import Path
from typing import Iterator, List, Optional, Sequence

from ..discovery.skill import AutoDiscovery
from ..entities import GitHubSource, LocalSource, Skill, Source
from ..progress import ProgressCallback
from ..functions.tag_filter import filter_skills_by_tags

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


def _normalize_github_sources(sources: Sequence[Source]) -> Iterator[Source]:
    """Yield sources, splitting GitHub sources with a list subpath.

    Возвращает источники, разбивая GitHub-источники со списком подпутей.

    A single :class:`GitHubSource` always refers to exactly one scan location.
    If the legacy list form is used, it is expanded into multiple instances
    so that each subpath is scanned independently.

    Один :class:`GitHubSource` всегда ссылается ровно на одну локацию
    сканирования. Если используется устаревшая форма списка, она разворачивается
    в несколько экземпляров, чтобы каждый подпуть сканировался независимо.
    """
    for src in sources:
        if isinstance(src, GitHubSource) and isinstance(src.subpath, list):
            for sp in src.subpath:
                yield GitHubSource(
                    repo_url=src.repo_url,
                    tree=src.tree,
                    subpath=sp,
                    tags=src.tags,
                )
        else:
            yield src


def discover(
    sources: Sequence[Source],
    progress: Optional[ProgressCallback] = None,
) -> List[Skill]:
    """Discover skills from a list of sources.

    Discover skills from a list of sources.

    Обнаружить навыки из списка источников.

    Args:
        sources: Skill sources to scan. / Источники навыков для сканирования.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        List of discovered ``Skill`` objects. / Список обнаруженных объектов ``Skill``.

    Raises:
        ValueError: If an unknown source type is encountered.
        ValueError: Если встречен неизвестный тип источника.
    """
    all_skills: List[Skill] = []
    normalized_sources = list(_normalize_github_sources(sources))

    logger.debug("Discovering skills from %d source(s)", len(normalized_sources))

    if progress is not None:
        progress("discover", 0, len(normalized_sources))

    for index, src in enumerate(normalized_sources, start=1):
        # Local paths are resolved to absolute form before scanning.
        # Локальные пути разрешаются в абсолютную форму перед сканированием.
        if isinstance(src, LocalSource):
            src = LocalSource(
                scan_path=Path(src.scan_path).resolve(),
                repo_path=Path(src.repo_path).resolve() if src.repo_path else None,
                original_repo_path=Path(src.original_repo_path).resolve()
                if src.original_repo_path
                else None,
                tags=src.tags,
            )

        scan_location = src.get_scan_location()
        logger.debug(
            "Source %d/%d: %s (type=%s)",
            index,
            len(normalized_sources),
            src,
            src.source_type,
        )
        logger.debug(
            "Resolved scan location: repo_path=%s source_path=%s",
            scan_location.repo_path,
            scan_location.source_path,
        )
        strategy = AutoDiscovery(
            source_path=scan_location.source_path,
            source=src,
        )
        source_skills = strategy.discover()
        logger.debug(
            "Source %d/%d discovered %d skill(s)",
            index,
            len(normalized_sources),
            len(source_skills),
        )

        if src.tags:
            source_skills = filter_skills_by_tags(source_skills, src.tags)
            logger.debug(
                "Source %d/%d retained %d skill(s) after tag filter",
                index,
                len(normalized_sources),
                len(source_skills),
            )

        all_skills.extend(source_skills)
        if progress is not None:
            progress("discover", index, len(normalized_sources))

    # EN: Remove duplicate skills discovered from overlapping sources.
    # RU: Убираем дублирующиеся навыки, обнаруженные из пересекающихся источников.
    seen: set[Path] = set()
    deduplicated: List[Skill] = []
    for skill in all_skills:
        if skill.file_path in seen:
            continue
        seen.add(skill.file_path)
        deduplicated.append(skill)

    return deduplicated
