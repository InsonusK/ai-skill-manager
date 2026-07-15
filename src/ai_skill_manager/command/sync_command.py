"""Orchestrates a sync run: discover -> enrich -> report/stop -> copy.

Оркестрирует запуск синхронизации: обнаружение -> обогащение ->
отчёт/остановка -> копирование.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, TYPE_CHECKING

from ..functions.file_discovery import FileDiscovery
from ..functions.skill_dict_builder import SkillDictBuilder
from ..functions.skill_discovery import SkillDiscovery

if TYPE_CHECKING:
    from ..entities import Source
    from ..entities.skill_v2 import Skill
    from ..functions.copy_skills.abs_copy_skills import CopySkills


@dataclass(frozen=True)
class SyncTarget:
    """One configured sync destination and how to copy into it.

    Одна настроенная цель синхронизации и способ копирования в неё.
    """

    name: str
    path: Path
    copy_skills: "CopySkills"


@dataclass(frozen=True)
class SyncResult:
    """Outcome of a sync run.

    Результат запуска синхронизации.
    """

    skills: List["Skill"]
    errors: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Return whether the run collected any errors."""
        return bool(self.errors)


class SyncCommand:
    """Runs discover -> enrich -> (report errors, stop) -> copy for one sync.

    Запускает discover -> enrich -> (отчёт об ошибках, остановка) -> copy
    для одной синхронизации.

    Contains no business rules of its own beyond sequencing: each step's
    logic lives in its own unit (``SkillDiscovery``, ``SkillDictBuilder``,
    ``FileDiscovery``, the configured ``CopySkills`` per target).

    Не содержит собственных бизнес-правил, кроме последовательности: логика
    каждого шага живёт в своём юните (``SkillDiscovery``,
    ``SkillDictBuilder``, ``FileDiscovery``, настроенный ``CopySkills`` на
    каждый target).
    """

    def __init__(
        self,
        skill_discovery: SkillDiscovery = None,
        skill_dict_builder: SkillDictBuilder = None,
        file_discovery: FileDiscovery = None,
    ) -> None:
        """Initialize with the discovery/enrichment collaborators."""
        self._skill_discovery = skill_discovery or SkillDiscovery()
        self._skill_dict_builder = skill_dict_builder or SkillDictBuilder()
        self._file_discovery = file_discovery or FileDiscovery()

    def run(
        self,
        sources: Sequence["Source"],
        targets: Sequence[SyncTarget],
        source_repo_path: Path,
        dry_run: bool,
        add_relations: bool,
    ) -> SyncResult:
        """Run one sync: discover, enrich, and (unless errors or dry_run) copy.

        Запускает одну синхронизацию: обнаруживает, обогащает и (если нет
        ошибок и это не dry_run) копирует.
        """
        discovered, errors = self._skill_discovery.discover(sources)
        skills, dict_errors = self._skill_dict_builder.build(discovered)
        errors.extend(dict_errors)

        queue: List["Skill"] = list(skills.values())
        processed_names = set()
        merged_count = len(queue)
        index = 0

        while index < len(queue):
            skill = queue[index]
            index += 1
            if skill.name in processed_names:
                continue
            processed_names.add(skill.name)

            if len(queue) > merged_count:
                skills, merge_errors = self._skill_dict_builder.build(queue[merged_count:], existing=skills)
                errors.extend(merge_errors)
                merged_count = len(queue)

            file_errors = self._file_discovery.discover(
                skill, repo_path=source_repo_path, known_skills=skills, queue=queue, add_relations=add_relations,
            )
            errors.extend(file_errors)

        if errors:
            return SyncResult(skills=list(skills.values()), errors=errors)

        if not dry_run:
            for target in targets:
                target.copy_skills.copy(
                    skills, target.path, source_repo_path=source_repo_path, output_repo_path=target.path,
                )

        return SyncResult(skills=list(skills.values()), errors=[])
