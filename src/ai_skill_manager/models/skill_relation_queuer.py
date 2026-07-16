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
    """Owns the queue of skills discovered via links during one sync run.

    Queues a not-yet-loaded skill for discovery, or reports why it can't be.
    Encapsulates both the growing ``queue`` (so a caller such as
    ``SyncCommand`` can walk it by index while it grows) and the
    ``add_relations`` policy for the run, so collaborators several layers
    away (e.g. ``FileLinkResolver`` in ``service.link_discovery``) never need
    to know about ``add_relations`` themselves - they just call
    :meth:`handle`.

    Владеет очередью скиллов, обнаруженных через ссылки за один запуск
    синхронизации. Ставит в очередь на обнаружение ещё не загруженный
    скилл, либо сообщает, почему это невозможно. Инкапсулирует как растущую
    ``queue`` (чтобы вызывающий код, например ``SyncCommand``, мог обходить
    её по индексу по мере роста), так и политику ``add_relations`` для
    запуска, поэтому сотрудничающим компонентам на несколько слоёв ниже
    (например, ``FileLinkResolver`` в ``service.link_discovery``) никогда не
    нужно знать про ``add_relations`` самим - они просто вызывают
    :meth:`handle`.

    Attributes:
        queue: Skills queued for discovery this run, in queue order. Grows
            in place as :meth:`handle` queues new candidates.
            / Скиллы, поставленные в очередь на обнаружение в этом запуске,
            в порядке очереди. Растёт на месте по мере того, как
            :meth:`handle` ставит в очередь новых кандидатов.
        add_relations: Whether linked-to skills outside the configured
            sources may be auto-discovered.
            / Разрешено ли автообнаружение скиллов, на которые есть
            ссылки, но которые находятся вне настроенных источников.
    """

    def __init__(self, add_relations: bool, queue: Optional[List["Skill"]] = None) -> None:
        """Initialize with the run's ``add_relations`` policy and starting queue.

        Args:
            add_relations: Whether linked-to skills outside the configured
                sources may be auto-discovered. / Разрешено ли
                автообнаружение скиллов вне настроенных источников.
            queue: Initial queue contents, typically the skills already
                found by source discovery. Defaults to an empty list.
                / Начальное содержимое очереди, обычно скиллы, уже
                найденные при обнаружении источников. По умолчанию - пустой
                список.
        """
        self.add_relations = add_relations
        self.queue: List["Skill"] = queue if queue is not None else []

    def handle(self, candidate: "Skill") -> QueueDecision:
        """Queue ``candidate`` by name, honoring ``self.add_relations``.

        Ставит ``candidate`` в очередь по имени, учитывая ``self.add_relations``.

        Args:
            candidate: Skill discovered at the link's target path.
                / Скилл, обнаруженный по целевому пути ссылки.

        Returns:
            The decision: queued, no-op (already queued), or an error.
                / Решение: поставлен в очередь, no-op (уже в очереди) или ошибка.
        """
        for queued_skill in self.queue:
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

        if not self.add_relations:
            return QueueDecision(
                queued=False,
                error=(
                    f"Link points to skill {candidate.name!r} at {candidate.path}, "
                    f"which is not part of the configured sources (add_relations is disabled)"
                ),
            )

        self.queue.append(candidate)
        return QueueDecision(queued=True)
