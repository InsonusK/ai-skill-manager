from abc import ABC,abstractmethod
from typing import Dict, List

from ...models.skill import Skill
from ..models.validation_result import ValidationResult

class absRule(ABC):
    @property
    @abstractmethod
    def name(self)->str:
        ...
    
    @abstractmethod
    def validate(self, skills:List[Skill])->Dict[Skill,ValidationResult]:
        ...
        
    