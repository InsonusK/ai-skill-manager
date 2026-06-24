"""Shared helpers for parsing source-related CLI arguments.

Provides a single place where ``--config``, ``--type``, ``--path`` and
``--subpath`` are resolved into a list of :class:`Source` objects.

Общие помощники для разбора аргументов CLI, связанных с источниками.
Предоставляет единое место, где ``--config``, ``--type``, ``--path`` и
``--subpath`` превращаются в список объектов :class:`Source`.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from ...config import build_sources_from_config
from ...entities import GitHubSource, LocalSource, Source

DEFAULT_CONFIG = "ai-skills.yaml"
#: Default config file name. / Имя файла конфигурации по умолчанию.

_DEFAULT_GITHUB_SUBPATHS = ["skills"]
#: Default subpath for GitHub sources when no --subpath is given.
#: Подпуть GitHub по умолчанию, если --subpath не указан.


def _parse_github_path(path: str) -> Tuple[str, str]:
    """Split a GitHub source path into repository URL and tree.

    Supports the ``<url> <tree>`` notation where the branch/tag is separated
    from the URL by a space. If no tree is provided, ``master`` is used.

    Разделяет путь к источнику GitHub на URL репозитория и ветку.
    Поддерживает нотацию ``<url> <tree>``, где ветка/тег отделена от URL
    пробелом. Если ветка не указана, используется ``master``.

    Args:
        path: Raw ``--path`` value for a GitHub source.
            Сырое значение ``--path`` для GitHub-источника.

    Returns:
        Tuple of ``(repo_url, tree)``. / Кортеж ``(repo_url, tree)``.
    """
    stripped = path.strip()
    parts = stripped.split(maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return stripped, "master"


def build_sources_from_args(args) -> Tuple[List[Source], Optional[Path]]:
    """Resolve CLI source arguments into sources and optional config path.

    Resolution order:
    1. Explicit ``--config``.
    2. Direct source mode via ``--type`` + ``--path``.
    3. Default config file ``ai-skills.yaml`` in the current directory.

    Преобразует аргументы CLI источников в сами источники и опциональный
    путь к файлу конфигурации.

    Порядок разрешения:
    1. Явный ``--config``.
    2. Прямой режим источника через ``--type`` + ``--path``.
    3. Файл конфигурации по умолчанию ``ai-skills.yaml`` в текущей директории.

    Args:
        args: Parsed argparse namespace. / Разобранное пространство имён argparse.

    Returns:
        ``(sources, config_path)`` where ``config_path`` is set only when a
        config file was used.

        ``(sources, config_path)``, где ``config_path`` заполнен только если
        использовался файл конфигурации.

    Raises:
        FileNotFoundError: If the requested config file does not exist.
            / Если запрошенный файл конфигурации не существует.
        ValueError: If ``--type`` is given without ``--path`` or is unknown.
            / Если ``--type`` указан без ``--path`` или неизвестен.
    """
    config = getattr(args, "config", None)
    source_type = getattr(args, "type", None)
    path = getattr(args, "path", None)
    subpaths = getattr(args, "subpath", None)

    if config:
        config_path = Path(config).resolve()
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        return build_sources_from_config(config_path), config_path

    if source_type:
        if not path:
            raise ValueError("--path is required when using --type")

        if source_type == "github":
            repo_url, tree = _parse_github_path(path)
            if subpaths is None:
                subpaths = _DEFAULT_GITHUB_SUBPATHS
            sources: List[Source] = [
                GitHubSource(repo_url=repo_url, tree=tree, subpath=sp)
                for sp in subpaths
            ]
        elif source_type in ("auto", "local"):
            sources = [LocalSource(scan_path=Path(path))]
        else:
            raise ValueError(f"Unknown source type: {source_type}")

        return sources, None

    # Default: try the config file in the current directory.
    # По умолчанию пробуем файл конфигурации в текущей директории.
    config_path = Path(DEFAULT_CONFIG).resolve()
    if config_path.exists():
        return build_sources_from_config(config_path), config_path

    raise FileNotFoundError(f"Config not found: {config_path}")
