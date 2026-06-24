"""Synchronization service.

Сервис синхронизации.
"""

from logging import Logger, ERROR, WARNING
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Type

from ..utils import compute_skill_hash, is_managed, write_managed_state

from ..adapters import Adapter
from ..adapters.rules import DEFAULT_RULES, LinkAdapter, absAdapter
from ..entities import LocalSource, Skill, Source
from ..entities.skill_format import SkillFormat
from ..validators import ValidationFailedError, Validator
from .discover import discover

logger = Logger("run_sync")


def run_sync(
    sources: Sequence[Source],
    target_dir: Path,
    adapters: Optional[Sequence[Type[absAdapter]]] = None,
    dry_run: bool = False,
    cleanup_orphans: bool = True,
    on_conflict: str = "error",
) -> dict:
    """Discover, validate, copy and adapt all skills.

    Discover, validate, copy and adapt all skills.

    Обнаруживает, валидирует, копирует и адаптирует все скиллы.

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
        on_conflict: Conflict resolution strategy (``error`` or ``last_wins``).
            Стратегия разрешения конфликтов (``error`` или ``last_wins``).

    Returns:
        Summary dict with counts and the target directory.
        Сводный словарь с количеством и целевой директорией.
    """
    skills: List[Skill] = discover(sources)

    try:
        validate_conflicts(on_conflict, skills)

        # Validate all discovered skills before copying anything.
        # Валидируем все обнаруженные навыки перед копированием.
        validator = Validator()
        validation_report = validator.validate(skills)
        if validation_report.has_errors:
            raise ValidationFailedError(validation_report)

        target_dir = Path(target_dir).resolve()

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
        links_replaced = 0
        # Capture validator versions for the managed state file.
        # Сохраняем версии валидаторов для файла управляемого состояния.
        validator_versions = [
            {
                "name": registered_rule[0],
                "version": registered_rule[1]() if callable(registered_rule[1]) else registered_rule[1],
            }
            for registered_rule in validator.registered_rules_name_version
        ]

        adapter_list = list(adapters) if adapters is not None else DEFAULT_RULES

        # Copy each skill into the target directory.
        # Копируем каждый навык в целевую директорию.
        for skill in skills:
            name = skill.properties.name
            if name is None:
                raise ValueError(
                    f"Skill {skill.file_path} has no 'name' in frontmatter")

            skill_target_dir = target_dir / name
            if skill.is_flat():
                new_skill = _copy_flat_skill(skill, skill_target_dir)
            else:
                new_skill = _copy_dir_skill(skill, skill_target_dir)

            copied_skills.append(new_skill)

        # Run adapters on the copied skills and count replaced links.
        # Запускаем адаптеры на скопированных навыках и считаем заменённые ссылки.
        adapter = Adapter(copied_skills, adapter_list)
        adapters_version = [
            {"name": registered_adapter[0],
             "version": registered_adapter[1]}
            for registered_adapter in adapter.registered_adapters_name_version
        ]
        for old_skill, new_skill in zip(skills, copied_skills):
            adapter_msg = adapter.adapt(old_skill, new_skill)
            link_msg = adapter_msg.get(LinkAdapter.name())
            if link_msg is not None:
                links_replaced += link_msg.params.get("count", 0)

        # Persist managed state for each copied skill.
        # Сохраняем управляемое состояние для каждого скопированного навыка.
        for new_skill in copied_skills:
            state = {
                "hash": compute_skill_hash(new_skill),
                "validators": validator_versions,
                "adapters": adapters_version
            }
            write_managed_state(new_skill.folder_path, state)

        # Remove previously copied skills that are no longer present.
        # Удаляем ранее скопированные навыки, которых больше нет в источниках.
        if cleanup_orphans:
            remove_orphans(target_dir, copied_skills)

        return {
            "skills_count": len(skills),
            "target_dir": str(target_dir),
            "links_replaced": links_replaced,
        }
    finally:
        # Release temporary resources acquired by remote sources.
        # Освобождаем временные ресурсы, полученные удалёнными источниками.
        for src in sources:
            src.cleanup()


def validate_conflicts(on_conflict: str, skills: List[Skill]):
    """
    Validate conflict naming in skills
    Проверяем конфликтующие названия в скилах
    """    
    # Validate conflict resolution strategy before doing real work.
    # Проверяем стратегию разрешения конфликтов перед выполнением основной работы.
    if on_conflict not in ("error", "last_wins"):
        raise ValueError(f"Invalid on_conflict value: {on_conflict}")

    # Detect duplicate skill names according to the chosen conflict strategy.
    # Обнаруживаем повторяющиеся имена навыков в соответствии с выбранной стратегией.
    seen_names: Dict[str, List[Skill]] = {}
    for skill in skills:
        name = skill.properties.name
        seen_skills: List[Skill] = seen_names.get(name, [])
        seen_skills.append(skill)
        seen_names[name] = seen_skills

    more_than_one_seen = {name: ss for name,
                          ss in seen_names.items() if len(ss) > 1}
    conflict_error_level = WARNING if on_conflict == "last_wins" else ERROR
    if len(more_than_one_seen) > 0:
        for name, seen_skills in more_than_one_seen.items():
            paths = "\n".join(f"  - {s.file_path}" for s in seen_skills)
            count = len(seen_skills)
            logger.log(
                conflict_error_level,
                f"CONFLICT: {count} skills have the same name %s:\n%s", name, paths
            )
        if on_conflict != "last_wins":
            raise ValueError(
                f"CONFLICT: {len(more_than_one_seen)} skills have the same name")


def remove_orphans(target_dir: Path, copied_skills: Sequence[Skill]) -> List[Path]:
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
    for entry in target_dir.iterdir():
        if not entry.is_dir():
            continue
        if not is_managed(entry):
            continue
        if entry in copied_dirs:
            continue
        shutil.rmtree(entry)
        removed.append(entry)
    return removed


def _copy_flat_skill(skill: Skill, skill_target_dir: Path) -> Skill:
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
    shutil.copy2(skill.file_path, target_path)
    return _build_target_skill(target_path, skill_target_dir)


def _copy_dir_skill(skill: Skill, skill_target_dir: Path) -> Skill:
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

    # Recursively copy every file, renaming the main skill file to SKILL.md.
    # Рекурсивно копируем каждый файл, переименовывая основной файл навыка в SKILL.md.
    for src_file in sorted(source_root.rglob("*")):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(source_root)
        if src_file.resolve() == skill.file_path.resolve():
            dst = skill_target_dir / "SKILL.md"
        else:
            dst = skill_target_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst)

    return _build_target_skill(skill_target_dir / "SKILL.md", skill_target_dir)


def _build_target_skill(file_path: Path, folder_path: Path) -> Skill:
    """Build a Skill object for a copied Agent-format skill.

    Build a Skill object for a copied Agent-format skill.

    Создаёт объект ``Skill`` для скопированного скилла в формате Agent.

    Args:
        file_path: Path to the skill's SKILL.md file. /
            Путь к файлу SKILL.md навыка.
        folder_path: Path to the skill's target directory. /
            Путь к целевой директории навыка.

    Returns:
        A new :class:`Skill` instance representing the copied skill. /
        Новый экземпляр :class:`Skill`, представляющий скопированный навык.
    """
    source_path = folder_path.parent
    source = LocalSource(scan_path=source_path)
    return Skill(
        file_path=file_path,
        folder_path=folder_path,
        source_path=source_path,
        source=source,
        format=SkillFormat.Agent,
    )
