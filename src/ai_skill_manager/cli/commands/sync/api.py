"""Sync command API.

Provides a pure function to run synchronization and return a result dictionary.
No console output is produced here.

Предоставляет чистую функцию для запуска синхронизации и возврата словаря
результата. Здесь не производится консольный вывод.
"""

from pathlib import Path
from typing import Optional

from ....config import build_sources_from_config, load_config
from ....services.sync import run_sync as run_sync_service

DEFAULT_CONFIG = "ai-skills.yaml"
#: Default config file name. / Имя файла конфигурации по умолчанию.

DEFAULT_TARGET = ".agents/skills"
#: Default target directory. / Целевая директория по умолчанию.


def run_sync(
    config_path: Path,
    target_dir: Optional[Path] = None,
    on_conflict: str = "error",
    remove_orphans: Optional[bool] = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """Run synchronization and return the result dictionary.

    Запускает синхронизацию и возвращает словарь результата.

    Args:
        config_path: Path to the configuration file. / Путь к файлу конфигурации.
        target_dir: Optional override for the target directory. /
            Опциональное переопределение целевой директории.
        on_conflict: Conflict resolution strategy (``error`` or ``last_wins``). /
            Стратегия разрешения конфликтов (``error`` или ``last_wins``).
        remove_orphans: Whether to remove orphan skills. Defaults to ``True``. /
            Удалять ли осиротевшие навыки. По умолчанию ``True``.
        dry_run: If ``True``, do not write any changes. /
            Если ``True``, не записывать изменения.
        force: If ``True``, skip hash and version checks. /
            Если ``True``, пропустить проверку хеша и версии.

    Returns:
        Result dictionary from the sync service. / Словарь результата от сервиса синхронизации.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
            / Если файл конфигурации не существует.
        ValueError: If an invalid configuration is encountered.
            / Если встречена некорректная конфигурация.

    Example:
        >>> from pathlib import Path
        >>> run_sync(Path("ai-skills.yaml"), dry_run=True)
        {'skills_count': 0, 'target_dir': '...', 'links_replaced': 0, 'dry_run': True}
    """
    config_path = config_path.resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    config = load_config(config_path)
    settings = config.get("settings", {})

    # Resolve target directory: CLI override > config > default.
    # Определяем целевую директорию: CLI > конфиг > умолчание.
    if target_dir is None:
        target_dir = Path(settings.get("target", DEFAULT_TARGET))
    if not target_dir.is_absolute():
        target_dir = config_path.parent / target_dir
    target_dir = target_dir.resolve()

    # Resolve orphan removal: CLI override > config > default.
    # Определяем удаление осиротевших навыков: CLI > конфиг > умолчание.
    if remove_orphans is None:
        remove_orphans = settings.get("remove_orphans", True)

    # Build sources from the configuration file.
    # Формируем источники из файла конфигурации.
    sources = build_sources_from_config(config_path)

    # Validate conflict strategy.
    # Проверяем стратегию разрешения конфликтов.
    if on_conflict not in ("error", "last_wins"):
        raise ValueError(f"Invalid on_conflict value: {on_conflict}")

    # The service handles conflict errors by raising ValueError.
    # Conflict resolution beyond error reporting is not yet supported.
    # Сервис обрабатывает конфликты, выбрасывая ValueError.
    # Разрешение конфликтов кроме ошибки пока не поддерживается.
    result = run_sync_service(
        sources=sources,
        target_dir=target_dir,
        dry_run=dry_run,
        cleanup_orphans=remove_orphans,
        on_conflict=on_conflict,
    )

    # Preserve legacy fields for formatters and callers.
    # Сохраняем устаревшие поля для форматёров и вызывающих сторон.
    result.setdefault("dry_run", dry_run)
    result.setdefault("skipped_count", 0)
    result.setdefault("synced_count", result.get("skills_count", 0))

    return result
