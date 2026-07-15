"""Sync command business logic.

Provides a pure function to run synchronization and return a result dictionary.
No console output is produced here.

Предоставляет чистую функцию для запуска синхронизации и возврата словаря
результата. Здесь не производится консольный вывод.
"""

from pathlib import Path
from typing import List, Optional, Sequence

from .sync_command import SyncCommand, SyncTarget
from ..config import (
    TargetSpec,
    build_sources_from_config,
    load_config,
    parse_target_settings,
)
from ..entities import Source
from ..functions.copy_skills import (
    IncrementalCopySkills,
    OrphanRemovingCopySkills,
    resolve_copy_skills,
)
from ..sync_exception import SyncFailedError

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
            copy_skills=resolve_copy_skills(["link-adapter"]),
        )
    ]


def run_sync(
    config_path: Optional[Path] = None,
    sources: Optional[Sequence[Source]] = None,
    target_dir: Optional[Path] = None,
    remove_orphans: Optional[bool] = None,
    dry_run: bool = False,
    force: bool = False,
    add_relations: Optional[bool] = None,
    progress=None,
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
        force: If ``True``, ignore the incremental hash-skip and re-copy
            every skill. / Если ``True``, игнорировать инкрементальный
            hash-skip и копировать каждый скилл заново.
        add_relations: Whether a link to a skill outside the configured
            sources auto-queues that skill for discovery. Defaults to the
            config's ``settings.add_relations`` (``False`` if unset).
            / Приводит ли ссылка на скилл вне настроенных источников к
            автоматической постановке этого скилла в очередь на
            обнаружение. По умолчанию берётся из
            ``settings.add_relations`` конфигурации (``False``, если не
            задано).
        progress: Unused; kept for CLI call-site compatibility.
            / Не используется; сохранён для совместимости вызова из CLI.

    Returns:
        Result dictionary with the discovered/synced skills.
            / Словарь результата с обнаруженными/синхронизированными скиллами.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
            / Если файл конфигурации не существует.
        ValueError: If neither ``config_path`` nor ``sources`` is provided,
            or if ``settings.target`` is malformed.
            / Если не указан ни ``config_path``, ни ``sources``, либо
            ``settings.target`` некорректен.
        SyncFailedError: If any skill failed a structural check or failed to
            resolve a link. ``target_dir`` is left untouched.
            / Если какой-либо скилл не прошёл структурную проверку или не
            смог разрешить ссылку. ``target_dir`` остаётся нетронутым.

    Example:
        >>> from pathlib import Path
        >>> run_sync(config_path=Path("ai-skills.yaml"), dry_run=True)
        {'skills_count': 0, 'dry_run': True, 'skills': []}
    """
    if config_path is None and sources is None:
        raise ValueError("Either config_path or sources must be provided")

    resolved_sources: Sequence[Source]
    config_base: Optional[Path] = None
    targets: List[TargetSpec]

    if config_path is not None:
        config_path = config_path.resolve()
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        config_base = config_path.parent

        if sources is None:
            config = load_config(config_path)
            settings = config.get("settings", {})

            # Resolve target(s): CLI override > config > default.
            # Определяем target(ы): CLI > конфиг > умолчание.
            if target_dir is not None:
                targets = _single_target(target_dir)
            else:
                targets = parse_target_settings(settings.get("target"))

            # Resolve orphan removal / add_relations: CLI override > config > default.
            # Определяем удаление осиротевших навыков / add_relations: CLI > конфиг > умолчание.
            if remove_orphans is None:
                remove_orphans = settings.get("remove_orphans", True)
            if add_relations is None:
                add_relations = settings.get("add_relations", False)

            resolved_sources = build_sources_from_config(config_path)
        else:
            resolved_sources = sources
            targets = _single_target(target_dir)
    else:
        resolved_sources = sources  # type: ignore[assignment]
        targets = _single_target(target_dir)

    if remove_orphans is None:
        remove_orphans = True
    if add_relations is None:
        add_relations = False

    base = config_base if config_base is not None else Path.cwd()

    sync_targets: List[SyncTarget] = []
    for spec in targets:
        path = spec.path if spec.path.is_absolute() else base / spec.path
        path = path.resolve()

        copy_skills = IncrementalCopySkills(
            spec.copy_skills,
            version=f"{type(spec.copy_skills).__name__}-1",
            force=force,
        )
        if remove_orphans:
            copy_skills = OrphanRemovingCopySkills(copy_skills)

        sync_targets.append(SyncTarget(name=spec.name, path=path, copy_skills=copy_skills))

    try:
        result = SyncCommand().run(
            sources=resolved_sources,
            targets=sync_targets,
            source_repo_path=base,
            dry_run=dry_run,
            add_relations=add_relations,
            output_repo_path=base,
        )
    finally:
        for src in resolved_sources:
            src.cleanup()

    if result.has_errors:
        raise SyncFailedError(result.errors, target_dir=sync_targets[0].path if sync_targets else base)

    return {
        "skills_count": len(result.skills),
        "dry_run": dry_run,
        "skills": result.skills,
        "targets": {target.name: {} for target in sync_targets},
    }
