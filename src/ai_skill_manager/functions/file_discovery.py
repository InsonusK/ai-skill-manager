"""Build one skill's file list and enrich its markdown files with links.

Implements step 2 (per-skill): the outer processing-queue loop across all
skills belongs to the orchestrator (``SyncCommand``), not this unit.

Строит список файлов одного скилла и обогащает его markdown-файлы ссылками.

Реализует шаг 2 (для одного скилла): внешний цикл обработки очереди по всем
скиллам принадлежит оркестратору (``SyncCommand``), а не этому юниту.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from ..entities.skill_file_v2 import MarkdownSkillFile, SkillFile
from ..entities.skill_kind import SkillKind
from ..validation_settings import ValidationSettings
from .link_discovery import LinkDiscovery

if TYPE_CHECKING:
    from ..entities.skill_v2 import Skill


class FileDiscovery:
    """Populates one skill's ``files`` and their links - implements step 2.

    Заполняет ``files`` одного скилла и их ссылки - реализует шаг 2.
    """

    def __init__(self, validation_settings: Optional[ValidationSettings] = None) -> None:
        """Initialize with the LinkDiscovery collaborator."""
        self._link_discovery = LinkDiscovery(validation_settings)

    def discover(
        self,
        skill: "Skill",
        repo_path: Path,
        known_skills: Dict[str, "Skill"],
        queue: List["Skill"],
        add_relations: bool,
    ) -> List[str]:
        """Populate ``skill.files`` in place and enrich markdown files with links.

        Заполняет ``skill.files`` на месте и обогащает markdown-файлы
        ссылками.

        Returns:
            Any errors collected while resolving links; discovery does not
            stop at the first one.
                / Ошибки, собранные при разрешении ссылок; обнаружение не
                останавливается на первой из них.
        """
        errors: List[str] = []

        if skill.kind is SkillKind.flat:
            skill.files.append(MarkdownSkillFile(name=skill.path.name, path=Path(".")))
        else:
            for candidate in sorted(skill.path.rglob("*")):
                if not candidate.is_file():
                    continue
                relative_path = candidate.relative_to(skill.path)
                if candidate.suffix.lower() == ".md":
                    skill.files.append(MarkdownSkillFile(name=candidate.name, path=relative_path))
                else:
                    skill.files.append(SkillFile(name=candidate.name, path=relative_path))

        for skill_file in skill.files:
            if not isinstance(skill_file, MarkdownSkillFile):
                continue
            file_absolute_path = skill.path if skill.kind is SkillKind.flat else skill.path / skill_file.path
            links, link_errors = self._link_discovery.discover(
                file_absolute_path,
                repo_path=repo_path,
                known_skills=known_skills,
                queue=queue,
                add_relations=add_relations,
            )
            skill_file.links.extend(links)
            errors.extend(link_errors)

        return errors
