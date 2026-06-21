
from pathlib import Path
from typing import List, Sequence

from ..entities import GitHubSource, LocalSource, Skill,Source
from ..discovery.skill import AutoDiscovery,GitHubDiscovery

STRATEGIES = {
    "auto": AutoDiscovery,
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
        if isinstance(src, GitHubSource):            
            subpath_value = src.subpath if src.subpath is not None else "skills"
            strategy = GitHubDiscovery(
                src.repo_url,
                tree=src.tree,
                subpath=subpath_value,
            )
        elif isinstance(src, LocalSource):
            strategy = AutoDiscovery(
                source_path=Path(src.path).resolve(),
                source=src
            )
        else:
            raise ValueError(f"Unknown type {src.source_type}")

        all_skills.extend(strategy.discover())

    return all_skills