from .models.validation_report import Skill, ValidationReport,Dict,ValidationResult
from .rules import absRule, DEFAULT_RULES,List

class Validator:
    
    def __init__(self, rule_list:List[absRule]=DEFAULT_RULES):
        rule_names = [r.name for r in rule_list]
        assert len(rule_names) == len(set(rule_names)), "Rules must have unique names"
        self.__rules = rule_list
        
    
    def validate(self, skills:List[Skill])->ValidationReport:
        report_dict: Dict[Skill,Dict[absRule, ValidationResult]] = {}
        
        for rule in self.__rules:
            rule_report = rule.validate(skills)
            for skill, result in rule_report.items():
                skill_validation_results = report_dict.get(skill,{})
                
                skill_validation_results[rule] = result
                
                report_dict[skill] = skill_validation_results
                
        return ValidationReport(report_dict)