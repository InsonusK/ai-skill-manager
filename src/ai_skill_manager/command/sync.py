"""Sync command business logic.

Provides a pure function to run synchronization and return a result dictionary.
No console output is produced here.

Предоставляет чистую функцию для запуска синхронизации и возврата словаря
результата. Здесь не производится консольный вывод.
"""

from pathlib import Path
from typing import Dict, List, Optional, Sequence

from ..adapters.rules import resolve_adapters
from ..config import (
    TargetSpec,
    build_sources_from_config,
    load_config,
    parse_target_settings,
    parse_validation_settings,
)
from ..validation_settings import ValidationSettings
from ..entities import Source
from ..progress import ProgressCallback
from ..service.discover import discover
from ..service.sync import sync_to_target

DEFAULT_TARGET = ".agents/skills"
#: Default target directory. / Целевая директория по умолчанию.


def _single_target(target_dir: Optional[Path]) -> List[TargetSpec]:
    """Build a single default-shaped target, matching pre-multi-target behavior.

    Строит один target в форме по умолчанию, соответствующей поведению до
    появления мульти-target.
    """
    return [
        TargetSpec(
            name="default",
            path=target_dir if target_dir is not None else Path(DEFAULT_TARGET),
            adapters=resolve_adapters(["link-adapter"]),
        )
    ]


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
            target(s) and orphan settings.
            / Путь к файлу конфигурации. Если ``sources`` не переданы,
            конфиг загружается и используется для источников, целевых
            директорий и настроек осиротевших навыков.
        sources: Optional explicit sources. If provided, ``config_path`` is
            only used to resolve relative target paths when it is also given.
            / Опциональные явные источники. Если переданы, ``config_path``
            используется только для разрешения относительных целевых путей.
        target_dir: Optional override for the target directory. When given,
            it replaces ``settings.target`` entirely with a single target
            using the default adapter list. / Опциональное переопределение
            целевой директории. Если передано, полностью заменяет
            ``settings.target`` одним target'ом со списком адаптеров по
            умолчанию.
        remove_orphans: Whether to remove orphan skills. Defaults to ``True``. /
            Удалять ли осиротевшие навыки. По умолчанию ``True``.
        dry_run: If ``True``, do not write any changes. /
            Если ``True``, не записывать изменения.
        force: If ``True``, skip hash and version checks. /
            Если ``True``, пропустить проверку хеша и версии.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        Result dictionary aggregated across all configured targets, plus a
        ``targets`` key with each target's individual result keyed by name.
        / Словарь результата, агрегированный по всем настроенным target'ам,
        плюс ключ ``targets`` с результатом каждого target'а по имени.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
            / Если файл конфигурации не существует.
        ValueError: If neither ``config_path`` nor ``sources`` is provided,
            or if ``settings.target`` is malformed.
            / Если не указан ни ``config_path``, ни ``sources``, либо
            ``settings.target`` некорректен.
        SyncFailedError: If any skill failed a structural check or failed to
            materialize into a target.
            / Если какой-либо скилл не прошёл структурную проверку или не
            материализовался в target.

    Example:
        >>> from pathlib import Path
        >>> run_sync(config_path=Path("ai-skills.yaml"), dry_run=True)
        {'skills_count': 0, 'skipped_count': 0, 'links_replaced': 0, 'targets': {}, 'dry_run': True, 'synced_count': 0, 'skills': []}
    """
    if config_path is None and sources is None:
        raise ValueError("Either config_path or sources must be provided")

    resolved_sources: Sequence[Source]
    config_base: Optional[Path] = None
    targets: List[TargetSpec]
    validation_settings: Optional[ValidationSettings] = None

    if config_path is not None:
        config_path = config_path.resolve()
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        config_base = config_path.parent

        if sources is None:
            config = load_config(config_path)
            settings = config.get("settings", {})
            validation_settings = parse_validation_settings(settings)

            # Resolve target(s): CLI override > config > default.
            # Определяем target(ы): CLI > конфиг > умолчание.
            if target_dir is not None:
                targets = _single_target(target_dir)
            else:
                targets = parse_target_settings(settings.get("target"))

            # Resolve orphan removal: CLI override > config > default.
            # Определяем удаление осиротевших навыков: CLI > конфиг > умолчание.
            if remove_orphans is None:
                remove_orphans = settings.get("remove_orphans", True)

            resolved_sources = build_sources_from_config(config_path)
        else:
            resolved_sources = sources
            targets = _single_target(target_dir)
    else:
        resolved_sources = sources  # type: ignore[assignment]
        targets = _single_target(target_dir)

    if remove_orphans is None:
        remove_orphans = True

    base = config_base if config_base is not None else Path.cwd()
    resolved_targets = []
    for spec in targets:
        path = spec.path
        if not path.is_absolute():
            path = base / path
        resolved_targets.append((spec.name, path.resolve(), spec.adapters))

    try:
        skills = discover(resolved_sources, progress=progress)
        per_target: Dict[str, dict] = {}
        for name, path, adapter_classes in resolved_targets:
            per_target[name] = sync_to_target(
                skills,
                path,
                adapters=adapter_classes,
                dry_run=dry_run,
                cleanup_orphans=remove_orphans,
                force=force,
                progress=progress,
                repo_path=base,
                settings=validation_settings,
            )
    finally:
        for src in resolved_sources:
            src.cleanup()

    result: dict = {
        "skills_count": len(skills),
        "skipped_count": sum(t.get("skipped_count", 0) for t in per_target.values()),
        "links_replaced": sum(t.get("links_replaced", 0) for t in per_target.values()),
        "targets": per_target,
        "skills": skills,
    }

    # Preserve legacy fields for formatters and callers.
    # Сохраняем устаревшие поля для форматёров и вызывающих сторон.
    result["dry_run"] = dry_run
    result.setdefault("synced_count", result.get("skills_count", 0))

    return result
