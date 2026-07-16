"""Build a FileLink (with its resolved target) from an already-parsed raw link.

Строит FileLink (с разрешённой целью) из уже распарсенной сырой ссылки.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, TYPE_CHECKING

from .link_target_resolver import LinkTargetResolver
from .raw_path_resolution import resolve_raw_link_path
from ...entities.link.file_link import FileLink
from ...entities.link.link_target import ExternalLinkTarget
from ...entities.skill_at_path_finder import SkillAtPathFinder

if TYPE_CHECKING:
    from ...entities.link.link_data import LinkData
    from ...entities.skill_v2 import Skill
    from ...models.skill_relation_queuer import SkillRelationQueuer

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


class FileLinkResolver:
    """Resolves one raw link's target - implements the ``2.1.1`` step.

    Разрешает цель одной сырой ссылки - реализует шаг ``2.1.1``.

    If the target belongs to an already-known skill, resolution is a plain
    lookup. If it belongs to a skill that has not been loaded yet, the
    caller-supplied ``SkillRelationQueuer`` decides whether to queue it or
    report an error - this class never needs to know ``add_relations``
    itself, since the queuer already carries that policy. Otherwise the
    target is treated as an external, non-skill file.

    Если цель принадлежит уже известному скиллу, резолюция - простой поиск.
    Если она принадлежит скиллу, который ещё не загружен, переданный
    вызывающей стороной ``SkillRelationQueuer`` решает, поставить ли его в
    очередь или сообщить об ошибке - этому классу никогда не нужно знать
    ``add_relations`` самому, так как queuer уже несёт эту политику. Иначе
    цель считается внешним файлом, не принадлежащим ни одному скиллу.
    """

    def __init__(self) -> None:
        """Initialize the collaborators used to resolve a link's target."""
        self._resolver = LinkTargetResolver()
        self._path_finder = SkillAtPathFinder()

    def build(
        self,
        raw_link: "LinkData",
        file_absolute_path: Path,
        repo_path: Path,
        known_skills: Dict[str, "Skill"],
        skill_relation_queuer: "SkillRelationQueuer",
    ) -> Tuple[Optional[FileLink], Optional[str]]:
        """Resolve ``raw_link`` and build the ``FileLink``, or report an error.

        Разрешает ``raw_link`` и строит ``FileLink``, либо сообщает об ошибке.

        Args:
            raw_link: Raw link data produced by syntax parsing, assumed to
                already have been classified as a file reference (not a web
                address) by the caller. / Сырые данные ссылки, полученные
                синтаксическим разбором, для которых вызывающий код уже
                определил, что это файловая ссылка (не веб-адрес).
            skill_relation_queuer: Owns this run's queue and
                ``add_relations`` policy for skills discovered via links.
                / Владеет очередью этого запуска и политикой
                ``add_relations`` для скиллов, обнаруженных через ссылки.

        Returns:
            ``(file_link, None)`` on success, or ``(None, error_message)``.
                / ``(file_link, None)`` при успехе, либо ``(None, сообщение_об_ошибке)``.
        """
        os_path = resolve_raw_link_path(raw_link.raw_path, file_absolute_path, repo_path)

        target = self._resolver.resolve(os_path, known_skills.values())

        if target is None:
            logger.debug(
                "Link %r did not match a known skill, searching for an "
                "unloaded skill owning %s", raw_link.raw, os_path
            )
            candidate = self._path_finder.find(os_path, repo_path)
            if candidate is not None:
                logger.info(
                    "Link %r resolved to unloaded skill %r at %s",
                    raw_link.raw, candidate.name, candidate.path,
                )
                decision = skill_relation_queuer.handle(candidate)
                if decision.error is not None:
                    return None, decision.error
                target = self._resolver.resolve(os_path, [candidate])
            else:
                logger.debug(
                    "No skill owns %s up to repo root %s, treating link %r as external",
                    os_path, repo_path, raw_link.raw,
                )

        if target is None:
            if not os_path.exists():
                return None, f"Link {raw_link.raw!r} points to a target that does not exist: {os_path}"
            target = ExternalLinkTarget(
                file_name=os_path.name,
                repo_absolute_path=Path(os.path.relpath(os_path, repo_path)),
            )

        file_link = FileLink(data=raw_link, target=target)
        return file_link, None
