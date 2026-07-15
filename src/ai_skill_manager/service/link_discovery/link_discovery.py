"""Find and resolve every link in a markdown file - implements step 2.1.

Поиск и разрешение всех ссылок в markdown-файле - реализует шаг 2.1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from ...discovery.link import search_links_in_content
from ...entities.link.file_link_factory import FileLinkFactory
from ...models import LinkWithContext
from ...validation_settings import ValidationSettings
from .exclude_rule import build_link_exclude_rules

if TYPE_CHECKING:
    from ...entities.link.file_link import FileLink
    from ...entities.skill_v2 import Skill


class LinkDiscovery:
    """Finds every link in one markdown file and resolves each one's target.

    Находит все ссылки в одном markdown-файле и разрешает цель каждой из них.

    Reuses the existing raw-link parser (regex-based, handles markdown and
    wiki syntax, ````example``` block masking) and the existing exclude
    rules (inline-code, web link, skip-folder) unchanged - only target
    *resolution* (:class:`FileLinkFactory`) is new.

    Переиспользует существующий парсер сырых ссылок (на основе regex,
    поддерживает markdown и wiki синтаксис, маскирование блоков
    ````example```) и существующие правила исключения (инлайн-код,
    веб-ссылка, пропускаемая директория) без изменений - новой является
    только *резолюция* цели (:class:`FileLinkFactory`).
    """

    def __init__(self, validation_settings: Optional[ValidationSettings] = None) -> None:
        """Initialize with the exclude rules configured by ``validation_settings``."""
        self._exclude_rules = build_link_exclude_rules(validation_settings)
        self._factory = FileLinkFactory()

    def discover(
        self,
        file_absolute_path: Path,
        repo_path: Path,
        known_skills: Dict[str, "Skill"],
        queue: List["Skill"],
        add_relations: bool,
    ) -> Tuple[List["FileLink"], List[str]]:
        """Discover and resolve the links in ``file_absolute_path``.

        Обнаруживает и разрешает ссылки в ``file_absolute_path``.

        Returns:
            Resolved links and any per-link resolution errors. Discovery
            does not stop at the first error - every link is attempted.
                / Разрешённые ссылки и ошибки резолюции по каждой ссылке.
                Обнаружение не останавливается на первой ошибке - каждая
                ссылка обрабатывается.
        """
        content = file_absolute_path.read_text(encoding="utf-8")
        raw_links = search_links_in_content(content)

        file_links: List["FileLink"] = []
        errors: List[str] = []

        for raw_link in raw_links:
            link_context = LinkWithContext.build(file_absolute_path, content, raw_link)
            if any(rule.should_exclude(link_context) for rule in self._exclude_rules):
                continue

            file_link, error = self._factory.build(
                raw_link,
                file_absolute_path=file_absolute_path,
                repo_path=repo_path,
                known_skills=known_skills,
                queue=queue,
                add_relations=add_relations,
            )
            if error is not None:
                errors.append(error)
                continue
            file_links.append(file_link)

        return file_links, errors
