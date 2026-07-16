"""Find and resolve every link in a markdown file - implements step 2.1.

Поиск и разрешение всех ссылок в markdown-файле - реализует шаг 2.1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from .link_factory import search_links_in_content
from .file_link_resolver import FileLinkResolver
from ...models import LinkWithContext, Result
from ...validation_settings import ValidationSettings
from .exclude_rule import build_link_exclude_rules

if TYPE_CHECKING:
    from ...entities.link.file_link import FileLink
    from ...entities.skill_v2 import Skill
    from ...models.skill_relation_queuer import SkillRelationQueuer


class LinkDiscovery:
    """Finds every link in one markdown file and resolves each one's target.

    Находит все ссылки в одном markdown-файле и разрешает цель каждой из них.

    Three collaborators split the work: ``link_factory`` finds raw links by
    syntax alone (markdown and wiki, ````example``` block masking), the
    exclude rules (inline-code, web link, skip-folder) filter out links that
    should not be resolved, and ``FileLinkResolver`` resolves the remaining
    (file) links' targets.

    Три сотрудничающих компонента разделяют работу: ``link_factory`` находит
    сырые ссылки чисто по синтаксису (markdown и wiki, маскирование блоков
    ````example```), правила исключения (инлайн-код, веб-ссылка, пропускаемая
    директория) отфильтровывают ссылки, которые не должны разрешаться, а
    ``FileLinkResolver`` разрешает цели оставшихся (файловых) ссылок.
    """

    def __init__(self, validation_settings: Optional[ValidationSettings] = None) -> None:
        """Initialize with the exclude rules configured by ``validation_settings``."""
        self._exclude_rules = build_link_exclude_rules(validation_settings)
        self._resolver = FileLinkResolver()

    def discover(
        self,
        file_absolute_path: Path,
        repo_path: Path,
        known_skills: Dict[str, "Skill"],
        skill_relation_queuer: "SkillRelationQueuer",
    ) -> Result[List["FileLink"]]:
        """Discover and resolve the links in ``file_absolute_path``.

        Обнаруживает и разрешает ссылки в ``file_absolute_path``.

        Args:
            skill_relation_queuer: Owns this run's queue and
                ``add_relations`` policy for skills discovered via links.
                / Владеет очередью этого запуска и политикой
                ``add_relations`` для скиллов, обнаруженных через ссылки.

        Returns:
            Resolved links and any per-link resolution errors. Discovery
            does not stop at the first error - every link is attempted.
                / Разрешённые ссылки и ошибки резолюции по каждой ссылке.
                Обнаружение не останавливается на первой ошибке - каждая
                ссылка обрабатывается.
        """
        content = file_absolute_path.read_text(encoding="utf-8")
        link_data_arr = search_links_in_content(content)

        file_links: List["FileLink"] = []
        errors: List[str] = []

        for link_data in link_data_arr:
            link_context = LinkWithContext.build(file_absolute_path, content, link_data)
            if any(rule.should_exclude(link_context) for rule in self._exclude_rules):
                continue

            file_link, error = self._resolver.build(
                link_data,
                file_absolute_path=file_absolute_path,
                repo_path=repo_path,
                known_skills=known_skills,
                skill_relation_queuer=skill_relation_queuer,
            )
            if error is not None:
                errors.append(error)
                continue
            file_links.append(file_link)

        return Result(file_links, errors)
