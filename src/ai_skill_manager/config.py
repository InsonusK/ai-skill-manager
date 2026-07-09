"""Configuration loading and source building.

Загрузка конфигурации и построение источников.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

from .adapters.rules import absAdapter, resolve_adapters
from .entities import GitHubSource, LocalSource, Source
from .validation_settings import ValidationSettings

#: Default target directory for the reserved "default" target name.
#: Целевая директория по умолчанию для зарезервированного имени "default".
#: Default target directory for the reserved "default" target name.
#: Целевая директория по умолчанию для зарезервированного имени "default".
DEFAULT_TARGET_PATH = ".agents/skills"

#: Default paths for reserved target names that omit ``path``.
#: Пути по умолчанию для зарезервированных имён target'ов без ``path``.
RESERVED_TARGET_DEFAULTS: Dict[str, str] = {
    "default": DEFAULT_TARGET_PATH,
    "claude": ".claude/skills",
}


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
        except ImportError:
            raise ImportError(
                "PyYAML required for .yaml files. Install: pip install pyyaml")

        from yaml import ScalarNode
        from yaml.constructor import ConstructorError

        class _ConfigYamlLoader(yaml.SafeLoader):
            """Loader that preserves unknown scalar tags as literal strings.

            Needed so tag expressions such as ``!web`` are not treated as
            YAML custom tags. / Загрузчик, который сохраняет неизвестные
            скалярные теги как строки, чтобы выражения вроде ``!web`` не
            воспринимались как пользовательские YAML-теги.
            """

        def _construct_unknown_scalar(loader, node):
            if not isinstance(node, ScalarNode):
                raise ConstructorError(
                    None,
                    None,
                    f"cannot construct non-scalar tag {node.tag!r}",
                    node.start_mark,
                )
            return f"{node.tag}{node.value}"

        _ConfigYamlLoader.add_constructor(None, _construct_unknown_scalar)
        return yaml.load(content, Loader=_ConfigYamlLoader)

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
        tags = _normalize_tags(src.get("tags"))

        # EN: GitHub sources are created from a repository URL and optional tree/subpath.
        # RU: Источники GitHub создаются из URL репозитория и опционального tree/subpath.
        skip_folders = _normalize_skip_folders(src.get("skip_folder"))

        if src_type == "github":
            for sp in _normalize_subpaths(src.get("subpath")):
                sources.append(
                    # BUG: если в github источнике нескольно subpath, то будет создано несколько GitHubSource каждый из которых будет скачивать репозитарий
                    #     необходиво подумать на разделением Source на Source (истоник) и ScanPackage (путь сканирования)
                    GitHubSource(
                        repo_url=src_path,
                        tree=src.get("tree", "master"),
                        subpath=sp,
                        tags=tags,
                        skip_folder=skip_folders,
                    )
                )
        elif src_type == "local":
            src_path = Path(src_path)
            # EN: Default to a local filesystem source resolved relative to the config file.
            # RU: По умолчанию используем локальный источник, разрешённый относительно файла конфигурации.
            repo_path = src_path if src_path.is_absolute() else config_dir / src_path
            for sp in _normalize_subpaths(src.get("subpath")):
                if sp is None:
                    sp_path = repo_path
                else:
                    sp_path = Path(sp)
                    if not sp_path.is_absolute():
                        sp_path = repo_path / sp_path
                sources.append(
                    LocalSource(
                        scan_path=sp_path,
                        repo_path=repo_path,
                        tags=tags,
                        skip_folder=skip_folders,
                    )
                )
        else:
            raise ValueError(f"Unkonwn {src_type}")

    return sources


@dataclass(frozen=True)
class TargetSpec:
    """A single sync destination: name, path and resolved adapter classes.

    Одна цель синхронизации: имя, путь и разрешённые классы адаптеров.
    """

    name: str
    path: Path
    adapters: List[Type[absAdapter]]


def _dedup_adapter_names(*name_lists: List[str]) -> List[str]:
    """Merge adapter name lists, keeping the first occurrence of each name.

    Объединяет списки имён адаптеров, сохраняя первое вхождение каждого имени.
    """
    seen: set[str] = set()
    merged: List[str] = []
    for names in name_lists:
        for name in names or []:
            if name not in seen:
                seen.add(name)
                merged.append(name)
    return merged


def parse_target_settings(target_value: Any) -> List[TargetSpec]:
    """Parse ``settings.target`` into a list of :class:`TargetSpec`.

    Разбирает ``settings.target`` в список :class:`TargetSpec`.

    Supports the legacy flat-string format (a single target using the
    default adapter) and the new multi-target mapping format with a
    reserved ``for_each`` key whose ``adapters`` are merged into every
    target's own adapter list.

    Поддерживает устаревший строковый формат (один target с адаптером по
    умолчанию) и новый формат с несколькими target'ами, где служебный ключ
    ``for_each`` задаёт адаптеры, добавляемые к адаптерам каждого target'а.

    Raises:
        ValueError: If the shape of ``target_value`` is invalid, a
            non-reserved target name is missing ``path``, or an adapter
            name is unknown.
            / Если форма ``target_value`` некорректна, нерезервированное
            имя target'а не имеет ``path``, либо имя адаптера неизвестно.
    """
    if target_value is None:
        target_value = DEFAULT_TARGET_PATH

    if isinstance(target_value, str):
        return [
            TargetSpec(
                name="default",
                path=Path(target_value),
                adapters=resolve_adapters(["link-adapter"]),
            )
        ]

    if not isinstance(target_value, dict):
        raise ValueError(
            "settings.target must be a string or a mapping, got "
            f"{type(target_value).__name__}"
        )

    raw = dict(target_value)
    for_each = raw.pop("for_each", None) or {}
    if not isinstance(for_each, dict):
        raise ValueError(
            "settings.target.for_each must be a mapping, got "
            f"{type(for_each).__name__}"
        )
    for_each_adapters = list(for_each.get("adapters") or [])

    if not raw:
        # Only for_each (or nothing) was given: fall back to a single
        # legacy-shaped default target.
        merged = for_each_adapters or ["link-adapter"]
        return [
            TargetSpec(
                name="default",
                path=Path(DEFAULT_TARGET_PATH),
                adapters=resolve_adapters(merged),
            )
        ]

    specs: List[TargetSpec] = []
    for name, entry in raw.items():
        entry = entry or {}
        if not isinstance(entry, dict):
            raise ValueError(
                f"settings.target.{name} must be a mapping, got "
                f"{type(entry).__name__}"
            )

        path_value = entry.get("path")
        if path_value is None:
            default_path = RESERVED_TARGET_DEFAULTS.get(name)
            if default_path is None:
                raise ValueError(
                    f"settings.target.{name} is missing required 'path' "
                    "(only reserved names "
                    f"{sorted(RESERVED_TARGET_DEFAULTS)} have a default path)"
                )
            path_value = default_path

        own_adapters = list(entry.get("adapters") or [])
        merged = _dedup_adapter_names(for_each_adapters, own_adapters)
        if not merged:
            merged = ["link-adapter"]

        specs.append(
            TargetSpec(
                name=name,
                path=Path(path_value),
                adapters=resolve_adapters(merged),
            )
        )

    return specs


def parse_validation_settings(settings: Any) -> ValidationSettings:
    """Parse ``settings.validation`` into :class:`ValidationSettings`.

    Разбирает ``settings.validation`` в :class:`ValidationSettings`.

    Args:
        settings: The ``settings`` section of the loaded config, or ``None``.
            / Секция ``settings`` загруженной конфигурации или ``None``.

    Returns:
        Parsed validation settings.
            / Разобранные настройки валидации.
    """
    if not isinstance(settings, dict):
        return ValidationSettings()

    validation = settings.get("validation") or {}
    if not isinstance(validation, dict):
        raise ValueError(
            "settings.validation must be a mapping, got "
            f"{type(validation).__name__}"
        )

    rules = validation.get("rules") or {}
    if not isinstance(rules, dict):
        raise ValueError(
            "settings.validation.rules must be a mapping, got "
            f"{type(rules).__name__}"
        )

    link_rules = rules.get("link") or {}
    if not isinstance(link_rules, dict):
        raise ValueError(
            "settings.validation.rules.link must be a mapping, got "
            f"{type(link_rules).__name__}"
        )

    skip_folder = link_rules.get("skip_folder")
    # YAML ``skip_folder:`` without a value loads as ``None``; treat it as an
    # explicit "no exclusions" together with an empty list.
    # YAML ``skip_folder:`` без значения загружается как ``None``; считаем это
    # явным отключением исключений вместе с пустым списком.
    if skip_folder is None:
        return ValidationSettings(link_skip_folders=None)
    if isinstance(skip_folder, list):
        return ValidationSettings(link_skip_folders=list(skip_folder))
    if isinstance(skip_folder, str):
        return ValidationSettings(link_skip_folders=[skip_folder])

    raise ValueError(
        "settings.validation.rules.link.skip_folder must be a list, string or null, "
        f"got {type(skip_folder).__name__}"
    )
