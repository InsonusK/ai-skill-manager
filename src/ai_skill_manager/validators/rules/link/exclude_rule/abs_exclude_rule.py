"""Base class for link validation exclude rules.

Базовый класс для правил исключения ссылок из валидации.
"""

from abc import ABC, abstractmethod
from typing import List

from .....models import LinkWithContext
from .....entities import Skill


class absExcludeRule(ABC):
    """Decides whether a link should be skipped by link validation/adaptation.

    Определяет, должна ли ссылка быть пропущена при валидации/адаптации ссылок.
    """

    @abstractmethod
    def should_exclude(self, link: LinkWithContext, skills: List[Skill]) -> bool:
        """Return ``True`` if the link must be skipped.

        Возвращает ``True``, если ссылку необходимо пропустить.

        Args:
            link: Link context to inspect.
                / Контекст ссылки для проверки.
            skills: All known skills, when needed for resolution.
                / Все известные навыки, если требуются для разрешения.

        Returns:
            Whether the link should be excluded from further checks.
                / Нужно ли исключить ссылку из дальнейших проверок.
        """
        ...
