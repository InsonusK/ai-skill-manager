"""Configuration loading and source building.

Загрузка конфигурации и построение источников.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from .entities import GitHubSource, LocalSource, Source


def load_config(config_path: Path) -> dict:
    """Load YAML or JSON config file."""
    content = config_path.read_text(encoding='utf-8')

    if config_path.suffix in ('.yaml', '.yml'):
        try:
            import yaml
            return yaml.safe_load(content)
        except ImportError:
            raise ImportError("PyYAML required for .yaml files. Install: pip install pyyaml")

    return json.loads(content)


def build_sources_from_config(config_path: Path) -> List[Source]:
    """Convert config sources into universal Source objects.

    Преобразует источники из конфигурации в универсальные объекты Source.

    Args:
        config_path: Path to the configuration file. / Путь к файлу конфигурации.

    Returns:
        List of Source objects. / Список объектов Source.
    """
    config = load_config(config_path)
    config_dir = config_path.parent
    sources: List[Source] = []

    for src in config.get("sources", []):
        src_type = src.get("type", "auto")
        src_path = src.get("path", "")

        if src_type == "github":
            sources.append(
                GitHubSource(
                    repo_url=src_path,
                    tree=src.get("tree", "master"),
                    subpath=src.get("subpath"),
                )
            )
        else:
            sources.append(
                LocalSource(path=Path(config_dir / src_path))
            )

    return sources
