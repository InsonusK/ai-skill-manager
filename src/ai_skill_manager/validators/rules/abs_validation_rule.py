from abc import ABC,abstractmethod
from typing import Dict, List

from ...entities.skill import Skill
from ..models.validation_result import ValidationResult

class absValidationRule(ABC):
    @property
    def version(self)->str:
        return ""
    @property
    def name(self)->str:
        return self.__class__.__name__
    
    @abstractmethod
    def validate(self, skills:List[Skill])->Dict[Skill,ValidationResult]:
        ...
        
    