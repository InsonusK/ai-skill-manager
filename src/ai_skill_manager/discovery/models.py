"""Input models for the discovery module."""

from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class Source:
    """Universal description of a skill source.

    The CLI/config wrapper converts every call variant (config file,
    single file path, directory path, GitHub URL) into one or more
    ``Source`` objects before calling ``discover()``.

    Универсальное описание источника навыков. Обёртка CLI/конфигурации
    преобразует любой вариант вызова в один или несколько объектов
    ``Source`` перед вызовом ``discover()``.
    """

    type: str
    #: Discovery strategy name: ``auto``, ``flat``, ``directory`` or ``github``.
    #: Имя стратегии обнаружения: ``auto``, ``flat``, ``directory`` или ``github``.

    path: str
    #: Local path or GitHub repository URL.
    #: Локальный путь или URL репозитория GitHub.

    tree: Optional[str] = "master"
    #: Git tree/branch for GitHub sources.
    #: Ветка/дерево Git для источников GitHub.

    subpath: Optional[Union[str, List[str]]] = None
    #: Subpath(s) inside a GitHub repository.
    #: Подпуть(и) внутри репозитория GitHub.

    name: Optional[str] = None
    #: Optional target-name override handled by sync, not discovery.
    #: Опциональное переопределение целевого имени; обрабатывается синхронизацией, а не discovery.
