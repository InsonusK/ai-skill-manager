"""Base class for file adapters."""

from abc import ABC, abstractmethod
from ...entities import Skill

class absAdapter(ABC):
    """Adapts files after copying to target."""

    @property
    def version(self)->str:
        return ""
    
    @property
    def name(self)->str:
        return self.__class__.__name__

    @abstractmethod
    def adapt(self, skill: Skill) -> None:
        """Modify file in place after copying."""
        ...
