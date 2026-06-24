"""Discovery service.

High-level helper that resolves each configured source to its scan location
and returns the combined list of skills.

Сервис обнаружения.
Высокоуровневый помощник, который разрешает каждый настроенный источник
в его локацию сканирования и возвращает объединённый список навыков.
"""

from pathlib import Path
from typing import Iterator, List, Sequence

from ..discovery.skill import AutoDiscovery
from ..entities import GitHubSource, LocalSource, Skill, Source


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
                )
        else:
            yield src


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

    for src in _normalize_github_sources(sources):
        # Local paths are resolved to absolute form before scanning.
        # Локальные пути разрешаются в абсолютную форму перед сканированием.
        if isinstance(src, LocalSource):
            src = LocalSource(
                scan_path=Path(src.scan_path).resolve(),
                repo_path=Path(src.repo_path).resolve() if src.repo_path else None,
            )

        scan_location = src.get_scan_location()
        strategy = AutoDiscovery(
            source_path=scan_location.source_path,
            source=src,
        )
        all_skills.extend(strategy.discover())

    return all_skills
