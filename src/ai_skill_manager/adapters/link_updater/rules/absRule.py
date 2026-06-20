"""Abstract base class for link transformation rules."""

from abc import ABC, abstractmethod

from ..models.Link import Link

from ..base import LinkContext


class LinkRule(ABC):
    """Base class for concrete link transformation rules."""

    @abstractmethod
    def match(self, link: Link) -> bool:
        """Check if this rule can handle the given link.

        Returns ``True`` if the link belongs to this rule's domain.
        """
        pass

    @abstractmethod
    def apply(self, link: Link, context: LinkContext) -> str:
        """Adapt the link to the target format.

        Returns the replacement link string.
        """
        pass
