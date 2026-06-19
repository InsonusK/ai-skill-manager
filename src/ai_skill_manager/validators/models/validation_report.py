from typing import Dict
from ..rules import absRule
from ...models.skill import Skill
from .validation_result import ValidationResult
from dataclasses import dataclass


@dataclass(slots=True)
class ValidationReport:
    result: Dict[Skill,Dict[absRule, ValidationResult]] = {}
    
    

