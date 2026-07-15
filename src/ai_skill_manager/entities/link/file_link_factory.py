"""Build a FileLink (with its resolved target) from an already-parsed raw link.

Строит FileLink (с разрешённой целью) из уже распарсенной сырой ссылки.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .file_link import FileLink
from .link_target import ExternalLinkTarget
from .link_target_resolver import LinkTargetResolver
from .raw_path_resolution import resolve_raw_link_path
from ..skill_at_path_finder import SkillAtPathFinder
from ...functions.skill_relation_queuer import SkillRelationQueuer

if TYPE_CHECKING:
    from ...entities.link.path_link import PathLink
    from ..skill_v2 import Skill


class FileLinkFactory:
    """Resolves one raw link's target - implements the ``2.1.1`` step.

    Разрешает цель одной сырой ссылки - реализует шаг ``2.1.1``.

    If the target belongs to an already-known skill, resolution is a plain
    lookup. If it belongs to a skill that has not been loaded yet,
    ``SkillRelationQueuer`` decides (via ``add_relations``) whether to queue
    it or report an error. Otherwise the target is treated as an external,
    non-skill file.

    Если цель принадлежит уже известному скиллу, резолюция - простой поиск.
    Если она принадлежит скиллу, который ещё не загружен, ``SkillRelationQueuer``
    решает (через ``add_relations``), поставить ли его в очередь или
    сообщить об ошибке. Иначе цель считается внешним файлом, не
    принадлежащим ни одному скиллу.
    """

    def __init__(self) -> None:
        """Initialize the collaborators used to resolve a link's target."""
        self._resolver = LinkTargetResolver()
        self._path_finder = SkillAtPathFinder()
        self._queuer = SkillRelationQueuer()

    def build(
        self,
        raw_link: "PathLink",
        file_absolute_path: Path,
        repo_path: Path,
        known_skills: Dict[str, "Skill"],
        queue: List["Skill"],
        add_relations: bool,
    ) -> Tuple[Optional[FileLink], Optional[str]]:
        """Resolve ``raw_link`` and build the ``FileLink``, or report an error.

        Разрешает ``raw_link`` и строит ``FileLink``, либо сообщает об ошибке.

        Returns:
            ``(file_link, None)`` on success, or ``(None, error_message)``.
                / ``(file_link, None)`` при успехе, либо ``(None, сообщение_об_ошибке)``.
        """
        os_path = resolve_raw_link_path(raw_link.path_raw.path, file_absolute_path, repo_path)

        target = self._resolver.resolve(os_path, known_skills.values())

        if target is None:
            candidate = self._path_finder.find(os_path)
            if candidate is not None:
                decision = self._queuer.handle(candidate, queue=queue, add_relations=add_relations)
                if decision.error is not None:
                    return None, decision.error
                target = self._resolver.resolve(os_path, [candidate])

        if target is None:
            if not os_path.exists():
                return None, f"Link {raw_link.raw!r} points to a target that does not exist: {os_path}"
            target = ExternalLinkTarget(
                file_name=os_path.name,
                repo_absolute_path=Path(os.path.relpath(os_path, repo_path)),
            )

        file_link = FileLink(
            raw=raw_link.raw,
            text=raw_link.text,
            format=raw_link.format,
            start=raw_link.start,
            end=raw_link.end,
            target=target,
            header=raw_link.header,
            is_image=raw_link.is_image,
        )
        return file_link, None
