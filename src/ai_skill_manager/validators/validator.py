from typing import Tuple

from .models.validation_report import Skill, ValidationReport,Dict,ValidationResult
from .rules import absValidationRule, DEFAULT_RULES,List

class Validator:
    
    def __init__(self, rule_list:List[absValidationRule]=DEFAULT_RULES):
        rule_names = [r.name for r in rule_list]
        assert len(rule_names) == len(set(rule_names)), "Rules must have unique names"
        self.__rules = rule_list
        
    @property
    def registered_rules_name_version(self) -> List[Tuple[str, str]]:
        return [(rule.name, rule.version) for rule in self.__rules]
    
    def validate(self, skills:List[Skill])->ValidationReport:
        report_dict: Dict[Skill,Dict[absValidationRule, ValidationResult]] = {}
        
        for rule in self.__rules:
            rule_report = rule.validate(skills)
            for skill, result in rule_report.items():
                skill_validation_results = report_dict.get(skill,{})
                
                skill_validation_results[rule] = result
                
                report_dict[skill] = skill_validation_results
                
        return ValidationReport(report_dict)