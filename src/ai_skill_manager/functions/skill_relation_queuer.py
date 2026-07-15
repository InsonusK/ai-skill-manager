"""Decide whether an unloaded, linked-to skill should be queued for discovery.

Решает, следует ли поставить в очередь на обнаружение незагруженный скилл,
на который есть ссылка.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.skill_v2 import Skill


@dataclass(frozen=True)
class QueueDecision:
    """Result of handling a candidate skill reference.

    Результат обработки ссылки на кандидата в скиллы.
    """

    queued: bool
    """``True`` if the candidate was newly added to the queue.
    ``True``, если кандидат был впервые добавлен в очередь."""

    error: Optional[str] = None
    """Error message, if the candidate could not be queued.
    Сообщение об ошибке, если кандидата не удалось поставить в очередь."""


class SkillRelationQueuer:
    """Queues a not-yet-loaded skill for discovery, or reports why it can't be.

    Ставит в очередь на обнаружение ещё не загруженный скилл, либо
    сообщает, почему это невозможно.
    """

    def handle(self, candidate: "Skill", queue: List["Skill"], add_relations: bool) -> QueueDecision:
        """Queue ``candidate`` by name, honoring ``add_relations``.

        Ставит ``candidate`` в очередь по имени, учитывая ``add_relations``.

        Args:
            candidate: Skill discovered at the link's target path.
                / Скилл, обнаруженный по целевому пути ссылки.
            queue: Skills already queued for discovery this run; mutated in
                place when a new skill is queued.
                / Скиллы, уже поставленные в очередь на обнаружение в этом
                запуске; изменяется на месте при постановке нового скилла.
            add_relations: Whether linked-to skills outside the configured
                sources may be auto-discovered.
                / Разрешено ли автообнаружение скиллов, на которые есть
                ссылки, но которые находятся вне настроенных источников.

        Returns:
            The decision: queued, no-op (already queued), or an error.
                / Решение: поставлен в очередь, no-op (уже в очереди) или ошибка.
        """
        for queued_skill in queue:
            if queued_skill.name == candidate.name:
                if queued_skill == candidate:
                    return QueueDecision(queued=False)
                return QueueDecision(
                    queued=False,
                    error=(
                        f"Cannot queue skill {candidate.name!r} at {candidate.path}: "
                        f"a different skill with the same name is already queued "
                        f"({queued_skill.path})"
                    ),
                )

        if not add_relations:
            return QueueDecision(
                queued=False,
                error=(
                    f"Link points to skill {candidate.name!r} at {candidate.path}, "
                    f"which is not part of the configured sources (add_relations is disabled)"
                ),
            )

        queue.append(candidate)
        return QueueDecision(queued=True)
