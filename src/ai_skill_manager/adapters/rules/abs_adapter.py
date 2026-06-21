"""Base class for file adapters."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple
from ...entities import Skill

class absAdapter(ABC):
    """Adapts files after copying to target."""
    @dataclass(frozen=True)
    class Context:
        skills:Tuple[Skill]
    
    def __init__(self, adapter_context:absAdapter.Context):
        self._adapter_context = adapter_context
        super().__init__()
        
    @classmethod
    def version(cls)->str:
        return ""
    
    @classmethod
    def name(cls)->str:
        return cls.__name__

    @abstractmethod
    def adapt(self, skill: Skill) -> None:
        """Modify file in place after copying."""
        ...
