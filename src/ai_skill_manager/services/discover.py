"""Discovery service.

High-level helper that routes each configured source to the appropriate
discovery strategy and returns the combined list of skills.

Сервис обнаружения.
Высокоуровневый помощник, который направляет каждый настроенный источник
в соответствующую стратегию обнаружения и возвращает объединённый список навыков.
"""

from pathlib import Path
from typing import List, Sequence

from ..entities import GitHubSource, LocalSource, Skill, Source
from ..discovery.skill import AutoDiscovery, GitHubDiscovery

# Mapping of source types to their discovery strategies.
# Сопоставление типов источников со стратегиями их обнаружения.
STRATEGIES = {
    "auto": AutoDiscovery,
    "github": GitHubDiscovery,
}


def discover(sources: Sequence[Source]) -> List[Skill]:
    """Discover skills from a list of sources.

    Discover skills from a list of sources.

    Обнаружить навыки из списка источников.

    Args:
        sources: Skill sources to scan. / Источники навыков для сканирования.

    Returns:
        List of discovered ``Skill`` objects. / Список обнаруженных объектов ``Skill``.

    Raises:
        ValueError: If an unknown source type is encountered.
        ValueError: Если встречен неизвестный тип источника.
    """
    all_skills: List[Skill] = []
    for src in sources:
        # Pick the strategy based on the concrete source type.
        # Выбираем стратегию на основе конкретного типа источника.
        if isinstance(src, GitHubSource):
            # GitHub repositories default to the ``skills`` subpath.
            # Репозитории GitHub по умолчанию используют подпуть ``skills``.
            subpath_value = src.subpath if src.subpath is not None else "skills"
            strategy = GitHubDiscovery(
                src.repo_url,
                tree=src.tree,
                subpath=subpath_value,
            )
        elif isinstance(src, LocalSource):
            strategy = AutoDiscovery(
                source_path=Path(src.path).resolve(),
                source=src,
            )
        else:
            raise ValueError(f"Unknown type {src.source_type}")

        all_skills.extend(strategy.discover())

    return all_skills
