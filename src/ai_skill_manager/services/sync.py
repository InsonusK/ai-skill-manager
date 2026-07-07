"""Synchronization service.

Сервис синхронизации.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Type

from ..entities.link.path_utils import same_path
from ..utils import compute_skill_hash, is_managed, read_managed_state, write_managed_state

from ..adapters import Adapter
from ..adapters.rules import DEFAULT_RULES, LinkAdapter, absAdapter
from ..entities import LocalSource, Skill, Source
from ..entities.skill_format import SkillFormat
from ..progress import ProgressCallback
from ..validators import ValidationFailedError, Validator
from .discover import discover

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


def discover_and_validate(
    sources: Sequence[Source],
    progress: Optional[ProgressCallback] = None,
) -> List[Skill]:
    """Discover skills from ``sources`` and validate them.

    Обнаруживает скиллы из ``sources`` и валидирует их.

    This is the target-independent half of a sync run: it does not touch
    any target directory, so it can be run once and its result reused for
    multiple targets.

    Это часть синхронизации, не зависящая от target'а: она не затрагивает
    целевую директорию, поэтому может быть выполнена один раз и переиспользована
    для нескольких target'ов.

    Args:
        sources: Sources to discover skills from.
            Источники для обнаружения скиллов.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        The discovered, validated skills. / Обнаруженные, валидированные скиллы.

    Raises:
        ValidationFailedError: If validation reports any errors.
            / Если валидация обнаружила ошибки.
    """
    logger.debug("Starting discovery: sources=%d", len(sources))
    skills: List[Skill] = discover(sources, progress=progress)
    logger.debug("Discovered %d skill(s)", len(skills))

    validator = Validator()
    validation_report = validator.validate(skills, progress=progress)
    if validation_report.has_errors:
        logger.debug("Validation failed with errors")
        raise ValidationFailedError(validation_report, skills=skills)
    logger.debug("Validation passed")

    return skills


def sync_to_target(
    skills: List[Skill],
    target_dir: Path,
    adapters: Optional[Sequence[Type[absAdapter]]] = None,
    dry_run: bool = False,
    cleanup_orphans: bool = True,
    force: bool = False,
    progress: Optional[ProgressCallback] = None,
    repo_path: Optional[Path] = None,
) -> dict:
    """Copy and adapt already-discovered skills into a single target directory.

    Копирует и адаптирует уже обнаруженные скиллы в одну целевую директорию.

    Args:
        skills: Skills discovered and validated via :func:`discover_and_validate`.
            Скиллы, обнаруженные и валидированные через :func:`discover_and_validate`.
        target_dir: Directory to copy the skills into.
            Директория, в которую копируются скиллы.
        adapters: Adapter classes to apply after copying.
            По умолчанию используется :data:`DEFAULT_RULES`.
            Классы адаптеров, применяемые после копирования.
        dry_run: If ``True``, do not write any changes.
            Если ``True``, не записывать изменения.
        cleanup_orphans: If ``True``, remove orphan skills from target.
            Если ``True``, удалять осиротевшие скиллы из целевой директории.
        force: If ``True``, ignore hash and adapter-version checks and copy
            every skill. / Если ``True``, игнорировать проверки хеша и версий
            адаптеров и копировать каждый скилл.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        Summary dict with counts and the target directory.
        Сводный словарь с количеством и целевой директорией.
    """
    logger.debug("Starting sync to target: target_dir=%s dry_run=%s force=%s", target_dir, dry_run, force)

    target_dir = Path(target_dir).resolve()
    if repo_path is None:
        repo_path = target_dir
    logger.debug("Resolved target_dir=%s repo_path=%s", target_dir, repo_path)

    # In dry-run mode return a summary without touching the filesystem.
    # В режиме dry-run возвращаем сводку, не затрагивая файловую систему.
    if dry_run:
        return {
            "skills_count": len(skills),
            "target_dir": str(target_dir),
            "links_replaced": 0,
            "dry_run": True,
        }

    target_dir.mkdir(parents=True, exist_ok=True)

    copied_skills: List[Skill] = []
    skills_to_adapt: List[Tuple[Skill, Skill]] = []
    source_hashes: Dict[Skill, str] = {}
    links_replaced = 0
    # Capture validator versions for the managed state file.
    # Сохраняем версии валидаторов для файла управляемого состояния.
    validator = Validator()
    validator_versions = [
        {
            "name": registered_rule[0],
            "version": registered_rule[1]() if callable(registered_rule[1]) else registered_rule[1],
        }
        for registered_rule in validator.registered_rules_name_version
    ]

    adapter_list = list(adapters) if adapters is not None else DEFAULT_RULES
    logger.debug("Adapters: %s", [a.__name__ for a in adapter_list])

    # Capture adapter versions before copying so we can skip skills that
    # have not changed since the last sync.
    # Запоминаем версии адаптеров до копирования, чтобы пропускать скиллы,
    # которые не изменились с последнего запуска.
    adapters_version = [
        {"name": registered_adapter[0],
         "version": registered_adapter[1]}
        for registered_adapter in Adapter([], adapter_list).registered_adapters_name_version
    ]

    # Copy each skill into the target directory.
    # Копируем каждый навык в целевую директорию.
    if progress is not None:
        progress("copy", 0, len(skills))
    for index, skill in enumerate(skills, start=1):
        name = skill.properties.name
        logger.debug("Processing skill %d/%d: name=%s file=%s format=%s", index, len(skills), name, skill.file_path, skill.format.value)
        if name is None:
            raise ValueError(
                f"Skill {skill.file_path} has no 'name' in frontmatter")

        skill_target_dir = target_dir / name
        source_hash = compute_skill_hash(skill)
        if not force and _is_skill_up_to_date(
                skill, skill_target_dir, adapters_version):
            logger.debug("Skill '%s' is up to date, skipping copy", name)
            new_skill = _build_target_skill(
                skill_target_dir / "SKILL.md", skill_target_dir, repo_path=repo_path)
        else:
            logger.debug("Skill '%s' needs copy (force=%s)", name, force)
            if skill.is_flat():
                new_skill = _copy_flat_skill(skill, skill_target_dir, repo_path=repo_path)
            else:
                new_skill = _copy_dir_skill(skill, skill_target_dir, repo_path=repo_path)
            skills_to_adapt.append((skill, new_skill))

        copied_skills.append(new_skill)
        source_hashes[new_skill] = source_hash
        if progress is not None:
            progress("copy", index, len(skills))

    # Run adapters only on skills that were actually copied.
    # Запускаем адаптеры только на тех скиллах, которые реально скопировались.
    skill_mapping = dict(zip(skills, copied_skills))
    copied_files: Dict[Path, Path] = {}
    adapter = Adapter(
        copied_skills,
        adapter_list,
        skill_mapping=skill_mapping,
        target_dir=target_dir,
        copied_files=copied_files,
    )
    logger.debug("Adapting %d copied skill(s)", len(skills_to_adapt))
    if progress is not None:
        progress("adapt", 0, len(skills_to_adapt))
    for index, (old_skill, new_skill) in enumerate(skills_to_adapt, start=1):
        logger.debug("Adapting skill: %s -> %s", old_skill.file_path, new_skill.file_path)
        adapter_msg = adapter.adapt(old_skill, new_skill)
        link_msg = adapter_msg.get(LinkAdapter.name())
        if link_msg is not None:
            links_replaced += link_msg.params.get("count", 0)
        if progress is not None:
            progress("adapt", index, len(skills_to_adapt))

    # Persist managed state for each copied skill.
    # The stored hash represents the *source* skill, so unchanged sources
    # can be detected on the next run.
    # Сохраняем управляемое состояние для каждого скопированного навыка.
    # Хранимый хеш относится к *исходному* скиллу, чтобы при следующем
    # запуске обнаружить неизменённые источники.
    logger.debug("Writing managed state for %d skill(s)", len(copied_skills))
    if progress is not None:
        progress("write_managed_state", 0, len(copied_skills))
    for index, new_skill in enumerate(copied_skills, start=1):
        state = {
            "hash": source_hashes[new_skill],
            "validators": validator_versions,
            "adapters": adapters_version
        }
        logger.debug("Managed state for %s: %s", new_skill.folder_path, state)
        _write_managed_state_if_changed(new_skill.folder_path, state)
        if progress is not None:
            progress("write_managed_state", index, len(copied_skills))

    # Remove previously copied skills that are no longer present.
    # Удаляем ранее скопированные навыки, которых больше нет в источниках.
    if cleanup_orphans:
        logger.debug("Removing orphan skills from %s", target_dir)
        remove_orphans(target_dir, copied_skills, progress=progress)

    logger.debug("Sync finished: %d skill(s), %d link(s) replaced", len(skills), links_replaced)
    return {
        "skills_count": len(skills),
        "target_dir": str(target_dir),
        "links_replaced": links_replaced,
        "skipped_count": len(skills) - len(skills_to_adapt),
    }


def run_sync(
    sources: Sequence[Source],
    target_dir: Path,
    adapters: Optional[Sequence[Type[absAdapter]]] = None,
    dry_run: bool = False,
    cleanup_orphans: bool = True,
    force: bool = False,
    progress: Optional[ProgressCallback] = None,
    repo_path: Optional[Path] = None,
) -> dict:
    """Discover, validate, copy and adapt all skills into a single target.

    Discover, validate, copy and adapt all skills into a single target.

    Обнаруживает, валидирует, копирует и адаптирует все скиллы в одну
    целевую директорию.

    Args:
        sources: Sources to discover skills from.
            Источники для обнаружения скиллов.
        target_dir: Directory to copy the skills into.
            Директория, в которую копируются скиллы.
        adapters: Adapter classes to apply after copying.
            По умолчанию используется :data:`DEFAULT_RULES`.
            Классы адаптеров, применяемые после копирования.
        dry_run: If ``True``, do not write any changes.
            Если ``True``, не записывать изменения.
        cleanup_orphans: If ``True``, remove orphan skills from target.
            Если ``True``, удалять осиротевшие скиллы из целевой директории.
        force: If ``True``, ignore hash and adapter-version checks and copy
            every skill. / Если ``True``, игнорировать проверки хеша и версий
            адаптеров и копировать каждый скилл.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        Summary dict with counts and the target directory.
        Сводный словарь с количеством и целевой директорией.
    """
    logger.debug("Starting sync: sources=%d target_dir=%s dry_run=%s force=%s", len(sources), target_dir, dry_run, force)
    try:
        skills = discover_and_validate(sources, progress=progress)
        return sync_to_target(
            skills,
            target_dir,
            adapters=adapters,
            dry_run=dry_run,
            cleanup_orphans=cleanup_orphans,
            force=force,
            progress=progress,
            repo_path=repo_path,
        )
    finally:
        # Release temporary resources acquired by remote sources.
        # Освобождаем временные ресурсы, полученные удалёнными источниками.
        for src in sources:
            src.cleanup()


def remove_orphans(
    target_dir: Path,
    copied_skills: Sequence[Skill],
    progress: Optional[ProgressCallback] = None,
) -> List[Path]:
    """Remove previously copied skills that are no longer present in sources.

    Remove previously copied skills that are no longer present in sources.

    Удаляет ранее скопированные скиллы, которых больше нет в исходных источниках.
    Учитываются только поддиректории целевой директории, помеченные файлом
    ``.ai-skills-managed``.

    Args:
        target_dir: Target directory containing copied skills.
            Целевая директория, содержащая скопированные скиллы.
        copied_skills: Skills that were copied during this sync run.
            Скиллы, скопированные в текущем запуске синхронизации.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        Paths of removed orphan directories. /
        Пути удалённых осиротевших директорий.
    """
    target_dir = Path(target_dir).resolve()
    copied_dirs = {
        Path(skill.folder_path).resolve()
        for skill in copied_skills
        if skill.folder_path is not None
    }
    removed: List[Path] = []
    # Iterate target entries and remove managed directories not in copied_skills.
    # Перебираем записи целевой директории и удаляем управляемые директории,
    # отсутствующие среди скопированных навыков.
    target_entries = list(target_dir.iterdir())
    logger.debug("Checking %d target entries for orphans", len(target_entries))
    if progress is not None:
        progress("remove_orphans", 0, len(target_entries))
    for index, entry in enumerate(target_entries, start=1):
        if entry.is_dir() and is_managed(entry) and entry.resolve() not in copied_dirs:
            logger.debug("Removing orphan skill directory: %s", entry)
            shutil.rmtree(entry)
            removed.append(entry)
        if progress is not None:
            progress("remove_orphans", index, len(target_entries))
    logger.debug("Removed %d orphan skill(s)", len(removed))
    return removed


def _is_skill_up_to_date(
    skill: Skill,
    skill_target_dir: Path,
    adapters_version: List[dict],
) -> bool:
    """Check if the target copy is still valid.

    Check if the target copy is still valid.

    Проверяет, актуальна ли целевая копия скилла.

    A skill is considered up-to-date when the target directory exists, was
    created by this tool, the source skill hash has not changed and the list
    of adapter versions is identical to the one stored in the managed state.

    Args:
        skill: Source skill to check. / Исходный скилл для проверки.
        skill_target_dir: Target directory used by a previous sync.
            Целевая директория из предыдущего запуска синхронизации.
        adapters_version: Current adapter versions to compare against.
            Текущие версии адаптеров для сравнения.

    Returns:
        ``True`` if copying and adapting can be skipped.
        ``True``, если копирование и адаптацию можно пропустить.
    """
    if not skill_target_dir.is_dir():
        logger.debug("Target dir missing: %s", skill_target_dir)
        return False

    target_skill_file = skill_target_dir / "SKILL.md"
    if not target_skill_file.is_file():
        logger.debug("Target SKILL.md missing: %s", target_skill_file)
        return False

    if not is_managed(skill_target_dir):
        logger.debug("Target dir is not managed: %s", skill_target_dir)
        return False

    state = read_managed_state(skill_target_dir)
    if state is None:
        logger.debug("No managed state for: %s", skill_target_dir)
        return False

    current_hash = compute_skill_hash(skill)
    up_to_date = (
        state.get("hash") == current_hash
        and state.get("adapters") == adapters_version
    )
    logger.debug(
        "Up-to-date check for %s: stored_hash=%s current_hash=%s stored_adapters=%s current_adapters=%s result=%s",
        skill_target_dir,
        state.get("hash"),
        current_hash,
        state.get("adapters"),
        adapters_version,
        up_to_date,
    )
    return up_to_date


def _write_managed_state_if_changed(skill_dir: Path, state: dict) -> None:
    """Write managed state only when it differs from the existing state.

    Write managed state only when it differs from the existing state.

    Записывает управляемое состояние только если оно отличается от уже
    существующего. Это избавляет от лишнего перетирания файла для скиллов,
    которые не изменились.
    """
    existing = read_managed_state(skill_dir)
    if existing == state:
        logger.debug("Managed state unchanged for %s, skipping write", skill_dir)
        return
    logger.debug("Writing managed state to %s", skill_dir)
    write_managed_state(skill_dir, state)


def _copy_flat_skill(skill: Skill, skill_target_dir: Path, repo_path: Path) -> Skill:
    """Copy a flat skill to the target directory as an Agent-format skill.

    Copy a flat skill to the target directory as an Agent-format skill.

    Копирует плоский скилл в целевую директорию в формате Agent.

    Args:
        skill: Flat skill to copy. / Плоский скилл для копирования.
        skill_target_dir: Destination directory for the skill. /
            Целевая директория для скилла.

    Returns:
        A new :class:`Skill` object pointing to the copied Agent-format file. /
        Новый объект :class:`Skill`, указывающий на скопированный файл в формате Agent.
    """
    skill_target_dir.mkdir(parents=True, exist_ok=True)
    target_path = skill_target_dir / "SKILL.md"
    logger.debug("Copying flat skill %s -> %s", skill.file_path, target_path)
    shutil.copy2(skill.file_path, target_path)
    return _build_target_skill(target_path, skill_target_dir, repo_path=repo_path)


def _copy_dir_skill(skill: Skill, skill_target_dir: Path, repo_path: Path) -> Skill:
    """Copy a directory skill to the target directory as an Agent-format skill.

    Copy a directory skill to the target directory as an Agent-format skill.

    Копирует директорию скилла в целевую директорию в формате Agent.

    Args:
        skill: Directory skill to copy. / Директориальный скилл для копирования.
        skill_target_dir: Destination directory for the skill. /
            Целевая директория для скилла.

    Returns:
        A new :class:`Skill` object pointing to the copied Agent-format directory. /
        Новый объект :class:`Skill`, указывающий на скопированную директорию в формате Agent.
    """
    assert skill.folder_path is not None

    source_root = skill.folder_path
    skill_target_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("Copying directory skill %s -> %s", source_root, skill_target_dir)

    # Recursively copy every file, renaming the main skill file to SKILL.md.
    # Рекурсивно копируем каждый файл, переименовывая основной файл навыка в SKILL.md.
    for src_file in sorted(source_root.rglob("*")):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(source_root)
        if same_path(src_file, skill.file_path):
            dst = skill_target_dir / "SKILL.md"
        else:
            dst = skill_target_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Copying skill file %s -> %s", src_file, dst)
        shutil.copy2(src_file, dst)

    return _build_target_skill(skill_target_dir / "SKILL.md", skill_target_dir, repo_path=repo_path)


def _build_target_skill(file_path: Path, folder_path: Path, repo_path: Path) -> Skill:
    """Build a Skill object for a copied Agent-format skill.

    Build a Skill object for a copied Agent-format skill.

    Создаёт объект ``Skill`` для скопированного скилла в формате Agent.

    Args:
        file_path: Path to the skill's SKILL.md file. /
            Путь к файлу SKILL.md навыка.
        folder_path: Path to the skill's target directory. /
            Путь к целевой директории навыка.
        repo_path: Repository root used for repo-absolute link formatting. /
            Корень репозитория для формирования repo-absolute ссылок.

    Returns:
        A new :class:`Skill` instance representing the copied skill. /
        Новый экземпляр :class:`Skill`, представляющий скопированный навык.
    """
    source_path = folder_path.parent
    source = LocalSource(scan_path=source_path, repo_path=repo_path)
    return Skill(
        file_path=file_path,
        folder_path=folder_path,
        source_path=source_path,
        source=source,
        format=SkillFormat.Agent,
    )
