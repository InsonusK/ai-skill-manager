"""Synchronization service.

Сервис синхронизации.
"""

import shutil
from pathlib import Path
from typing import List, Optional, Sequence, Type

from ..utils import compute_skill_hash, is_managed, write_managed_state

from ..adapters import Adapter
from ..adapters.rules import DEFAULT_RULES, LinkAdapter, absAdapter
from ..entities import LocalSource, Skill, Source
from ..entities.skill_format import SkillFormat
from ..validators import ValidationFailedError, Validator
from .discover import discover


def run_sync(
    sources: Sequence[Source],
    target_dir: Path,
    adapters: Optional[Sequence[Type[absAdapter]]] = None
) -> dict:
    """Discover, validate, copy and adapt all skills.

    Обнаруживает, валидирует, копирует и адаптирует все скиллы.

    Args:
        sources: Sources to discover skills from.
            Источники для обнаружения скиллов.
        target_dir: Directory to copy the skills into.
            Директория, в которую копируются скиллы.
        adapters: Adapter classes to apply after copying.
            По умолчанию используется :data:`DEFAULT_RULES`.
            Классы адаптеров, применяемые после копирования.

    Returns:
        Summary dict with counts and the target directory.
        Сводный словарь с количеством и целевой директорией.
    """
    skills = discover(sources)

    validator = Validator()
    validation_report = validator.validate(skills)
    if validation_report.has_errors:
        raise ValidationFailedError(validation_report)

    target_dir = Path(target_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    copied_skills: List[Skill] = []
    links_replaced = 0
    validator_versions = [
        {
            "name": registered_rule[0],
            "version": registered_rule[1]() if callable(registered_rule[1]) else registered_rule[1],
        }
        for registered_rule in validator.registered_rules_name_version
    ]

    adapter_list = list(adapters) if adapters is not None else DEFAULT_RULES

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

    for new_skill in copied_skills:
        state = {
            "hash": compute_skill_hash(new_skill),
            "validators": validator_versions,
            "adapters": adapters_version
        }
        write_managed_state(new_skill.folder_path, state)

    remove_orphans(target_dir, copied_skills)

    return {
        "skills_count": len(skills),
        "target_dir": str(target_dir),
        "links_replaced": links_replaced,
    }


def remove_orphans(target_dir: Path, copied_skills: Sequence[Skill]) -> List[Path]:
    """Remove previously copied skills that are no longer present in sources.

    Удаляет ранее скопированные скиллы, которых больше нет в исходных источниках.
    Учитываются только поддиректории целевой директории, помеченные файлом
    ``.ai-skills-managed``.
    """
    target_dir = Path(target_dir).resolve()
    copied_dirs = {
        Path(skill.folder_path).resolve()
        for skill in copied_skills
        if skill.folder_path is not None
    }
    removed: List[Path] = []
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

    Копирует плоский скилл в целевую директорию в формате Agent.
    """
    skill_target_dir.mkdir(parents=True, exist_ok=True)
    target_path = skill_target_dir / "SKILL.md"
    shutil.copy2(skill.file_path, target_path)
    return _build_target_skill(target_path, skill_target_dir)


def _copy_dir_skill(skill: Skill, skill_target_dir: Path) -> Skill:
    """Copy a directory skill to the target directory as an Agent-format skill.

    Копирует директорию скилла в целевую директорию в формате Agent.
    """
    assert skill.folder_path is not None

    source_root = skill.folder_path
    skill_target_dir.mkdir(parents=True, exist_ok=True)

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

    Создаёт объект ``Skill`` для скопированного скилла в формате Agent.
    """
    source_path = folder_path.parent
    source = LocalSource(path=source_path)
    return Skill(
        file_path=file_path,
        folder_path=folder_path,
        source_path=source_path,
        source=source,
        format=SkillFormat.Agent,
    )
