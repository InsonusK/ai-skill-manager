"""Orchestrates a sync run: discover -> enrich -> report/stop -> copy.

Оркестрирует запуск синхронизации: обнаружение -> обогащение ->
отчёт/остановка -> копирование.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Sequence, TYPE_CHECKING

from ..entities.skill_file_v2 import MarkdownSkillFile
from ..functions.file_discovery import discover as discover_skill_files
from ..functions.link_discovery import LinkDiscovery
from ..functions.skill_dict_builder import SkillDictBuilder
from ..functions.skill_discovery import SkillDiscovery

if TYPE_CHECKING:
    from ..entities import Source
    from ..entities.skill_v2 import Skill
    from ..entities.skill_file_v2 import SkillFile
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
    ``file_discovery.discover``, ``LinkDiscovery``, the configured
    ``CopySkills`` per target). In particular, this is the seam between file
    discovery and link discovery: ``file_discovery.discover`` only finds and
    classifies a skill's files (a plain function - it holds no state and
    needs no collaborator), ``LinkDiscovery`` only resolves the links of one
    already-known markdown file - walking a skill's freshly-discovered files
    and calling ``LinkDiscovery`` for each markdown one is this
    orchestrator's job, kept here instead of nested inside file discovery so
    neither unit depends on the other.

    Не содержит собственных бизнес-правил, кроме последовательности: логика
    каждого шага живёт в своём юните (``SkillDiscovery``,
    ``SkillDictBuilder``, ``file_discovery.discover``, ``LinkDiscovery``,
    настроенный ``CopySkills`` на каждый target). В частности, это стык между
    обнаружением файлов и обнаружением ссылок: ``file_discovery.discover``
    только находит и классифицирует файлы скилла (простая функция - у неё
    нет состояния и не нужен коллаборатор), ``LinkDiscovery`` только
    разрешает ссылки одного уже известного markdown-файла - обход
    только что обнаруженных файлов скилла и вызов ``LinkDiscovery`` для
    каждого markdown-файла - задача этого оркестратора, оставленная здесь,
    а не вложенная внутрь обнаружения файлов, чтобы ни один из юнитов не
    зависел от другого.
    """

    def __init__(
        self,
        skill_discovery: SkillDiscovery = None,
        skill_dict_builder: SkillDictBuilder = None,
        file_discovery: Callable[["Skill"], List["SkillFile"]] = None,
        link_discovery: LinkDiscovery = None,
    ) -> None:
        """Initialize with the discovery/enrichment collaborators."""
        self._skill_discovery = skill_discovery or SkillDiscovery()
        self._skill_dict_builder = skill_dict_builder or SkillDictBuilder()
        self._file_discovery = file_discovery or discover_skill_files
        self._link_discovery = link_discovery or LinkDiscovery()

    def run(
        self,
        sources: Sequence["Source"],
        targets: Sequence[SyncTarget],
        source_repo_path: Path,
        dry_run: bool,
        add_relations: bool,
        output_repo_path: Optional[Path] = None,
    ) -> SyncResult:
        """Run one sync: discover, enrich, and (unless errors or dry_run) copy.

        Запускает одну синхронизацию: обнаруживает, обогащает и (если нет
        ошибок и это не dry_run) копирует.

        Args:
            output_repo_path: Repository root that rewritten link text is
                expressed relative to, shared by every target. Defaults to
                each target's own path (so a skill's links read as plain
                names like ``skill-b/SKILL.md``); pass an ancestor of every
                target to include their relative prefix instead.
                / Корень репозитория, относительно которого выражается
                текст переписанных ссылок, общий для всех target'ов. По
                умолчанию - собственный путь каждого target'а (тогда ссылки
                скилла выглядят как простые имена вроде
                ``skill-b/SKILL.md``); передайте предка всех target'ов,
                чтобы включить их относительный префикс.
        """
        skills, errors = self._skill_discovery.discover(sources)

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

            skill.files.extend(self._file_discovery(skill))

            for skill_file in skill.files:
                if not isinstance(skill_file, MarkdownSkillFile):
                    continue
                links, link_errors = self._link_discovery.discover(
                    skill.file_absolute_path(skill_file),
                    repo_path=source_repo_path,
                    known_skills=skills,
                    queue=queue,
                    add_relations=add_relations,
                )
                skill_file.links.extend(links)
                errors.extend(link_errors)

        if errors:
            return SyncResult(skills=list(skills.values()), errors=errors)

        if not dry_run:
            for target in targets:
                target.copy_skills.copy(
                    skills,
                    target.path,
                    source_repo_path=source_repo_path,
                    output_repo_path=output_repo_path if output_repo_path is not None else target.path,
                )

        return SyncResult(skills=list(skills.values()), errors=[])
