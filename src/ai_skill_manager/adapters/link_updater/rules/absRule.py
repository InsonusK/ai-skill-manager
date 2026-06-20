"""Abstract base class for link transformation rules."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from ..models import Link


class LinkRule(ABC):
    """Base class for concrete link transformation rules."""
    
    @abstractmethod
    def to_skill_format(self, link: Link) -> str:
        """Adapt the link to the target format.

        Returns the replacement link string.
        """
        pass
