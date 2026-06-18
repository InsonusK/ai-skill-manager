"""Sync command API.

Provides a pure function to run synchronization and return a result dictionary.
No console output is produced here.

Предоставляет чистую функцию для запуска синхронизации и возврата словаря
результата. Здесь не производится консольный вывод.
"""

from pathlib import Path
from typing import Optional

from ...core import SkillSync

DEFAULT_CONFIG = "ai-skills.yaml"
#: Default config file name. / Имя файла конфигурации по умолчанию.


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
        Result dictionary from ``SkillSync.sync()``. / Словарь результата от ``SkillSync.sync()``.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
            / Если файл конфигурации не существует.

    Example:
        >>> from pathlib import Path
        >>> run_sync(Path("ai-skills.yaml"), dry_run=True)
        {'synced_count': 0, 'skipped_count': 0, 'fix_summary': {}, 'fixes': [], 'dry_run': True}
    """
    config_path = config_path.resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    # Build the orchestrator with explicit CLI overrides.
    # Создаём оркестратор с явными переопределениями из CLI.
    sync = SkillSync(
        config_file=config_path,
        target_dir=target_dir,
        on_conflict=on_conflict,
        remove_orphans=remove_orphans if remove_orphans is not None else True,
        dry_run=dry_run,
        force=force,
    )
    return sync.sync()
