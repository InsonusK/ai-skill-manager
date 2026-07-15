"""Base class for link validation exclude rules.

Базовый класс для правил исключения ссылок из валидации.
"""

from abc import ABC, abstractmethod

from ....models import LinkWithContext


class absExcludeRule(ABC):
    """Decides whether a link should be skipped by link validation/adaptation.

    Определяет, должна ли ссылка быть пропущена при валидации/адаптации ссылок.
    """

    @abstractmethod
    def should_exclude(self, link: LinkWithContext) -> bool:
        """Return ``True`` if the link must be skipped.

        Возвращает ``True``, если ссылку необходимо пропустить.

        Args:
            link: Link context to inspect.
                / Контекст ссылки для проверки.

        Returns:
            Whether the link should be excluded from further checks.
                / Нужно ли исключить ссылку из дальнейших проверок.
        """
        ...
