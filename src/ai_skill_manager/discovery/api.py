"""Discovery public API.

Provides a single entry point to discover skills from a list of sources.
Discovery only finds skills; it does not decide where to copy them.

Предоставляет единую точку входа для обнаружения навыков из списка
источников. Discovery только ищет навыки, но не определяет, куда их
копировать.
"""

from pathlib import Path
from typing import List, Sequence

from ..models.skill import Skill
from .models import Source
from .source import AutoDiscovery, GitHubDiscovery

STRATEGIES = {
    "auto": AutoDiscovery,
    "flat": AutoDiscovery,
    "directory": AutoDiscovery,
    "github": GitHubDiscovery,
}


def discover(sources: Sequence[Source]) -> List[Skill]:
    """Discover skills from a list of sources.

    Args:
        sources: Skill sources to scan. / Источники навыков для сканирования.

    Returns:
        List of discovered ``Skill`` objects. / Список обнаруженных объектов ``Skill``.

    Raises:
        ValueError: If an unknown source type is encountered.
            / Если встречен неизвестный тип источника.
    """
    all_skills: List[Skill] = []
    for src in sources:
        strategy_class = STRATEGIES.get(src.type)
        if strategy_class is None:
            raise ValueError(f"Unknown source type: {src.type}")

        if src.type == "github":
            subpath_value = src.subpath if src.subpath is not None else "skills"
            strategy = GitHubDiscovery(
                src.path,
                tree=src.tree,
                subpath=subpath_value,
            )
        else:
            strategy = strategy_class(Path(src.path).resolve())

        all_skills.extend(strategy.discover())

    return all_skills
