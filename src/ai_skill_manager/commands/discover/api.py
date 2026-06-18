"""Discover command API.

Provides pure functions to discover skills from a config file or a single
source. All functions return data objects (lists of ``SkillMapping``) and do
not print anything.

Предоставляет чистые функции для обнаружения навыков из файла конфигурации
или одного источника. Все функции возвращают объекты данных (списки
``SkillMapping``) и ничего не выводят.
"""

from pathlib import Path
from typing import List, Optional

from ...config import load_config
from ...core import STRATEGIES
from ...discovery.base import SkillMapping
from ...discovery.github import GitHubDiscovery

DEFAULT_CONFIG = "ai-skills.yaml"
#: Default config file name. / Имя файла конфигурации по умолчанию.

DEFAULT_TARGET = ".agents/skills"
#: Default target directory. / Целевая директория по умолчанию.


def resolve_target(
    config_dir: Path, settings: dict, target_override: Optional[str] = None
) -> Path:
    """Resolve target directory from args, config settings, or default.

    Определяет целевую директорию из аргументов, настроек конфига или значения
    по умолчанию.

    Args:
        config_dir: Directory containing the config file. / Директория с файлом конфигурации.
        settings: ``settings`` section from the config. / Секция ``settings`` из конфига.
        target_override: Optional CLI override. / Опциональное переопределение из CLI.

    Returns:
        Absolute target directory. / Абсолютная целевая директория.
    """
    if target_override:
        return Path(target_override).resolve()
    if "target" in settings:
        return config_dir / settings["target"]
    return Path(DEFAULT_TARGET).resolve()


def discover_from_config(config_path: Path, target_dir: Path) -> List[SkillMapping]:
    """Discover skills from all sources in a config file.

    Обнаруживает навыки из всех источников в файле конфигурации.

    Args:
        config_path: Path to the config file. / Путь к файлу конфигурации.
        target_dir: Base target directory for mappings. / Базовая целевая директория для сопоставлений.

    Returns:
        List of discovered skill mappings. / Список обнаруженных сопоставлений навыков.

    Raises:
        ValueError: If an unknown source type is encountered.
            / Если встречен неизвестный тип источника.
    """
    config = load_config(config_path)
    config_dir = config_path.parent
    sources = config.get("sources", [])

    all_mappings: List[SkillMapping] = []
    for src in sources:
        src_type = src.get("type", "auto")
        strategy_class = STRATEGIES.get(src_type)
        if strategy_class is None:
            raise ValueError(f"Unknown source type: {src_type}")

        if src_type == "github":
            # GitHub source requires special handling with tree and subpath.
            # Источник GitHub требует особой обработки с веткой и подпутём.
            repo_url = src.get("path", "")
            tree = src.get("tree", "master")
            subpath = src.get("subpath", "skills")
            strategy = GitHubDiscovery(
                repo_url, target_dir, tree=tree, subpath=subpath
            )
        else:
            # Local sources are resolved relative to the config directory.
            # Локальные источники разрешаются относительно директории конфига.
            src_path = config_dir / src.get("path", ".")
            strategy = strategy_class(src_path, target_dir)

        all_mappings.extend(strategy.discover())

    return all_mappings


def discover_single_source(
    src_type: str,
    src_path: str,
    target_dir: Path,
    tree: str = "master",
    subpath: Optional[List[str]] = None,
) -> List[SkillMapping]:
    """Discover skills from a single command-line source.

    Обнаруживает навыки из одного источника, переданного через командную строку.

    Args:
        src_type: Discovery strategy name. / Имя стратегии обнаружения.
        src_path: Source path or GitHub URL. / Путь к источнику или URL GitHub.
        target_dir: Target directory for mappings. / Целевая директория для сопоставлений.
        tree: Git tree/branch for GitHub sources. / Ветка/дерево Git для источников GitHub.
        subpath: List of GitHub subpaths. / Список подпутей в GitHub.

    Returns:
        List of discovered skill mappings. / Список обнаруженных сопоставлений навыков.

    Raises:
        ValueError: If ``src_path`` is empty or source type is unknown.
            / Если ``src_path`` пустой или тип источника неизвестен.
    """
    if not src_path:
        raise ValueError("--path is required when using --type")

    strategy_class = STRATEGIES.get(src_type)
    if strategy_class is None:
        raise ValueError(f"Unknown source type: {src_type}")

    if src_type == "github":
        # Use the first subpath or fall back to the default "skills".
        # Используем первый подпуть или значение по умолчанию "skills".
        subpath_value = subpath[0] if subpath else "skills"
        strategy = GitHubDiscovery(
            src_path, target_dir, tree=tree, subpath=subpath_value
        )
    else:
        strategy = strategy_class(Path(src_path).resolve(), target_dir)

    return strategy.discover()
