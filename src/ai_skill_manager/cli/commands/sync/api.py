"""Sync command API.

Provides a pure function to run synchronization and return a result dictionary.
No console output is produced here.

Предоставляет чистую функцию для запуска синхронизации и возврата словаря
результата. Здесь не производится консольный вывод.
"""

from pathlib import Path
from typing import Optional, Sequence

from ....config import build_sources_from_config, load_config
from ....entities import Source
from ....progress import ProgressCallback
from ....services.sync import run_sync as run_sync_service

DEFAULT_CONFIG = "ai-skills.yaml"
#: Default config file name. / Имя файла конфигурации по умолчанию.

DEFAULT_TARGET = ".agents/skills"
#: Default target directory. / Целевая директория по умолчанию.


def run_sync(
    config_path: Optional[Path] = None,
    sources: Optional[Sequence[Source]] = None,
    target_dir: Optional[Path] = None,
    remove_orphans: Optional[bool] = None,
    dry_run: bool = False,
    force: bool = False,
    progress: Optional[ProgressCallback] = None,
) -> dict:
    """Run synchronization and return the result dictionary.

    Запускает синхронизацию и возвращает словарь результата.

    Args:
        config_path: Path to the configuration file. When ``sources`` is not
            provided, the config is loaded and used to resolve sources,
            target directory and orphan settings.
            / Путь к файлу конфигурации. Если ``sources`` не переданы,
            конфиг загружается и используется для источников, целевой
            директории и настроек осиротевших навыков.
        sources: Optional explicit sources. If provided, ``config_path`` is
            only used to resolve relative target paths when it is also given.
            / Опциональные явные источники. Если переданы, ``config_path``
            используется только для разрешения относительных целевых путей.
        target_dir: Optional override for the target directory. /
            Опциональное переопределение целевой директории.
        remove_orphans: Whether to remove orphan skills. Defaults to ``True``. /
            Удалять ли осиротевшие навыки. По умолчанию ``True``.
        dry_run: If ``True``, do not write any changes. /
            Если ``True``, не записывать изменения.
        force: If ``True``, skip hash and version checks. /
            Если ``True``, пропустить проверку хеша и версии.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        Result dictionary from the sync service. / Словарь результата от сервиса синхронизации.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
            / Если файл конфигурации не существует.
        ValueError: If neither ``config_path`` nor ``sources`` is provided.
            / Если не указан ни ``config_path``, ни ``sources``.

    Example:
        >>> from pathlib import Path
        >>> run_sync(config_path=Path("ai-skills.yaml"), dry_run=True)
        {'skills_count': 0, 'target_dir': '...', 'links_replaced': 0, 'dry_run': True}
    """
    if config_path is None and sources is None:
        raise ValueError("Either config_path or sources must be provided")

    resolved_sources: Sequence[Source]
    config_base: Optional[Path] = None

    if config_path is not None:
        config_path = config_path.resolve()
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        config_base = config_path.parent

        if sources is None:
            config = load_config(config_path)
            settings = config.get("settings", {})

            # Resolve target directory: CLI override > config > default.
            # Определяем целевую директорию: CLI > конфиг > умолчание.
            if target_dir is None:
                target_dir = Path(settings.get("target", DEFAULT_TARGET))
            if not target_dir.is_absolute():
                target_dir = config_base / target_dir

            # Resolve orphan removal: CLI override > config > default.
            # Определяем удаление осиротевших навыков: CLI > конфиг > умолчание.
            if remove_orphans is None:
                remove_orphans = settings.get("remove_orphans", True)

            resolved_sources = build_sources_from_config(config_path)
        else:
            resolved_sources = sources
    else:
        resolved_sources = sources  # type: ignore[assignment]

    if target_dir is None:
        target_dir = Path(DEFAULT_TARGET)
    if not target_dir.is_absolute():
        base = config_base if config_base is not None else Path.cwd()
        target_dir = base / target_dir
    target_dir = target_dir.resolve()

    if remove_orphans is None:
        remove_orphans = True

    result = run_sync_service(
        sources=resolved_sources,
        target_dir=target_dir,
        dry_run=dry_run,
        cleanup_orphans=remove_orphans,
        force=force,
        progress=progress,
    )

    # Preserve legacy fields for formatters and callers.
    # Сохраняем устаревшие поля для форматёров и вызывающих сторон.
    result.setdefault("dry_run", dry_run)
    result.setdefault("skipped_count", 0)
    result.setdefault("synced_count", result.get("skills_count", 0))

    return result
