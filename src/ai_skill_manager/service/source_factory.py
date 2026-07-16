"""Builds Source objects from individual parameters or a config file.

Строит объекты Source из отдельных параметров или файла конфигурации.
"""

from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

from ..config import load_config
from ..entities import GitHubSource, LocalSource, Source

DEFAULT_GITHUB_SUBPATHS: Tuple[str, ...] = ("skills",)
#: Default subpaths for a GitHub source when none are given.
#: Подпути GitHub по умолчанию, если ни один не указан.


def _normalize_subpaths(subpath: Any) -> Tuple[Optional[str], ...]:
    """Convert a subpath config value into a tuple of single subpaths.

    Преобразует значение подпути из конфигурации в кортеж отдельных подпутей.

    ``None`` and a single string become a tuple with one entry; a list is
    converted to a tuple unchanged.

    ``None`` и одиночная строка становятся кортежем с одним элементом;
    список преобразуется в кортеж без изменений.
    """
    if subpath is None:
        return (None,)
    if isinstance(subpath, (list, tuple)):
        return tuple(subpath)
    return (subpath,)


def _normalize_skip_folders(value: Any) -> Tuple[str, ...]:
    """Convert a skip_folder config value into a tuple of folder names.

    Преобразует значение skip_folder из конфигурации в кортеж имён директорий.

    ``None`` falls back to the default ``("examples",)``. A single string
    becomes a one-element tuple; a list is converted to a tuple of strings.
    An empty list disables folder-based exclusions.

    ``None`` заменяется умолчанием ``("examples",)``. Одиночная строка
    становится кортежем из одного элемента; список преобразуется в кортеж
    строк. Пустой список отключает исключения по директориям.
    """
    if value is None:
        return ("examples",)
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(folder) for folder in value)
    return (str(value),)


def _normalize_tags(tags: Any) -> Tuple[str, ...]:
    """Convert a tag filter config value into a tuple of expressions.

    Преобразует значение фильтра тегов из конфигурации в кортеж выражений.

    ``None`` becomes an empty tuple; a single string becomes a one-element
    tuple; a list is converted to a tuple of strings.

    ``None`` становится пустым кортежем; одиночная строка — кортежем из
    одного элемента; список преобразуется в кортеж строк.
    """
    if tags is None:
        return ()
    if isinstance(tags, str):
        return (tags,)
    if isinstance(tags, (list, tuple)):
        return tuple(str(tag) for tag in tags)
    return (str(tags),)


class SourceFactory:
    """Builds :class:`Source` objects.

    Строит объекты :class:`Source`.

    Two construction paths are supported: from individual parameters (as
    used by the CLI's direct ``--type``/``--path`` mode) and from a config
    file's ``sources`` section.

    Поддерживаются два способа построения: из отдельных параметров (как в
    прямом режиме CLI через ``--type``/``--path``) и из секции ``sources``
    файла конфигурации.
    """

    def create_from_params(
        self,
        source_type: str,
        path: str,
        subpath: Optional[Sequence[str]] = None,
        tree: str = "master",
    ) -> List[Source]:
        """Build sources from individually supplied parameters.

        Строит источники из отдельно переданных параметров.

        Args:
            source_type: ``"github"``, ``"local"`` or ``"auto"``.
                / ``"github"``, ``"local"`` или ``"auto"``.
            path: GitHub repository URL or local filesystem path.
                / URL репозитория GitHub или локальный путь файловой системы.
            subpath: Subpaths inside a GitHub repository to scan. Defaults to
                :data:`DEFAULT_GITHUB_SUBPATHS` when omitted.
                / Подпути внутри репозитория GitHub для сканирования. Если не
                указаны, используется :data:`DEFAULT_GITHUB_SUBPATHS`.
            tree: Git branch or tag for a GitHub source.
                / Ветка или тег Git для источника GitHub.

        Returns:
            A single-element list containing the built source.
            / Список из одного построенного источника.

        Raises:
            ValueError: If ``source_type`` is unknown.
                / Если ``source_type`` неизвестен.
        """
        if source_type == "github":
            subpaths = tuple(subpath) if subpath else DEFAULT_GITHUB_SUBPATHS
            return [GitHubSource(repo_url=path, tree=tree, subpaths=subpaths)]

        if source_type in ("auto", "local"):
            return [LocalSource(scan_paths=(Path(path).absolute(),))]

        raise ValueError(f"Unknown source type: {source_type}")

    def create_from_config(self, config_path: Path) -> List[Source]:
        """Build sources from a config file's ``sources`` section.

        Строит источники из секции ``sources`` файла конфигурации.

        Args:
            config_path: Path to the configuration file.
                / Путь к файлу конфигурации.

        Returns:
            List of Source objects. / Список объектов Source.

        Raises:
            ValueError: If a source entry has an unknown ``type``.
                / Если запись источника имеет неизвестный ``type``.
        """
        config = load_config(config_path)
        config_dir = config_path.parent
        sources: List[Source] = []

        for src in config.get("sources", []):
            src_type = src.get("type", "auto")
            src_path = src.get("path", "")
            tags = _normalize_tags(src.get("tags"))
            skip_folders = _normalize_skip_folders(src.get("skip_folder"))

            if src_type == "github":
                # A single GitHubSource downloads the repository once and
                # reuses it for every configured subpath.
                # Один GitHubSource скачивает репозиторий один раз и
                # переиспользует его для каждого настроенного подпути.
                sources.append(
                    GitHubSource(
                        repo_url=src_path,
                        tree=src.get("tree", "master"),
                        subpaths=_normalize_subpaths(src.get("subpath")),
                        tags=tags,
                        skip_folder=skip_folders,
                    )
                )
            elif src_type == "local":
                repo_root = Path(src_path)
                repo_path = (repo_root if repo_root.is_absolute() else config_dir / repo_root).absolute()
                scan_paths: List[Path] = []
                for sp in _normalize_subpaths(src.get("subpath")):
                    if sp is None:
                        scan_paths.append(repo_path)
                    else:
                        sp_path = Path(sp)
                        scan_paths.append((sp_path if sp_path.is_absolute() else repo_path / sp_path).absolute())
                sources.append(
                    LocalSource(
                        scan_paths=tuple(scan_paths),
                        repo_path=repo_path,
                        tags=tags,
                        skip_folder=skip_folders,
                    )
                )
            else:
                raise ValueError(f"Unkonwn {src_type}")

        return sources
