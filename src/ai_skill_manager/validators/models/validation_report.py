from typing import Dict, List
from ..rules import absValidationRule
from ...models.skill import Skill
from .validation_result import ValidationResult
from dataclasses import dataclass
from .validation_severity import ValidationSeverity

@dataclass(slots=True)
class ValidationReport:
    result: Dict[Skill,Dict[absValidationRule, ValidationResult]] = {}
    @property
    def has_errors(self)->bool:
        return any(
            vr.severity == ValidationSeverity.ERROR
            for skill_results in self.result.values()
            for vr in skill_results.values()
        )
    
    @property
    def errors(self) -> Dict[Skill,Dict[absValidationRule, ValidationResult]]:
        _return = {}
        for skill, rule_results in self.result.items():
            skill_errors = {}
            for rule, rule_result in rule_results.items():
                if rule_result.severity == ValidationSeverity.ERROR:
                    skill_errors[rule] = rule_result
            if len(skill_errors) > 0:
                _return[skill] = skill_errors
        return _return

