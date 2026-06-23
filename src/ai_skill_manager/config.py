"""Configuration loading and source building.

Загрузка конфигурации и построение источников.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from .entities import GitHubSource, LocalSource, Source


def load_config(config_path: Path) -> dict:
    """Load YAML or JSON config file.

    Загружает файл конфигурации в формате YAML или JSON.
    """
    # EN: Read the whole configuration file as text.
    # RU: Читаем весь файл конфигурации как текст.
    content = config_path.read_text(encoding='utf-8')

    # EN: Use PyYAML for YAML files; fall back to JSON for everything else.
    # RU: Используем PyYAML для YAML-файлов; для остальных — JSON.
    if config_path.suffix in ('.yaml', '.yml'):
        try:
            import yaml
            return yaml.safe_load(content)
        except ImportError:
            raise ImportError("PyYAML required for .yaml files. Install: pip install pyyaml")

    return json.loads(content)


def _normalize_subpaths(subpath: Any) -> List[str | None]:
    """Convert a subpath config value into a list of single subpaths.

    Преобразует значение подпути из конфигурации в список отдельных подпутей.

    ``None`` and a single string become a list with one entry; a list is
    returned unchanged.

    ``None`` и одиночная строка становятся списком с одним элементом;
    список возвращается без изменений.
    """
    if subpath is None:
        return [None]
    if isinstance(subpath, list):
        return subpath
    return [subpath]


def build_sources_from_config(config_path: Path) -> List[Source]:
    """Convert config sources into universal Source objects.

    Преобразует источники из конфигурации в универсальные объекты Source.

    Args:
        config_path: Path to the configuration file. / Путь к файлу конфигурации.

    Returns:
        List of Source objects. / Список объектов Source.
    """
    # EN: Load the raw configuration and remember its directory for relative paths.
    # RU: Загружаем сырую конфигурацию и запоминаем её директорию для относительных путей.
    config = load_config(config_path)
    config_dir = config_path.parent
    sources: List[Source] = []

    # EN: Iterate over the configured sources and create typed Source instances.
    # RU: Перебираем настроенные источники и создаём типизированные экземпляры Source.
    for src in config.get("sources", []):
        src_type = src.get("type", "auto")
        src_path = src.get("path", "")

        # EN: GitHub sources are created from a repository URL and optional tree/subpath.
        # RU: Источники GitHub создаются из URL репозитория и опционального tree/subpath.
        if src_type == "github":
            for sp in _normalize_subpaths(src.get("subpath")):
                sources.append(
                    GitHubSource(
                        repo_url=src_path,
                        tree=src.get("tree", "master"),
                        subpath=sp,
                    )
                )
        else:
            # EN: Default to a local filesystem source resolved relative to the config file.
            # RU: По умолчанию используем локальный источник, разрешённый относительно файла конфигурации.
            sources.append(
                LocalSource(path=Path(config_dir / src_path))
            )

    return sources
