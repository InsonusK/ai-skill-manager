from typing import Dict, Optional
from xml.dom import ValidationErr
from .abs_validation_rule import Skill, absValidationRule, ValidationResult, List
from ...entities import SkillFormat
from ..models import ValidationSeverity,ValidationError

class NameValidationRule(absValidationRule):
    def version(self)->str:
        return "1.0.0"
    
    def validate(self, skills: List[Skill]) -> Dict[Skill, ValidationResult]:
        results = {}
        for skill in skills:
            if skill.properties.name is None:
                results[skill] = ValidationResult.single(ValidationError("Name is not set in properties", ValidationSeverity.ERROR))
                continue

            if skill.format == SkillFormat.Agent:
                if (error := self.__validate_agent(skill)) is not None:
                    results[skill] = ValidationResult.single(error)
            elif skill.format == SkillFormat.HumanFlat:
                if (error := self.__validate_human_flat(skill)) is not None:
                    results[skill] = ValidationResult.single(error)
            elif skill.format == SkillFormat.HumanDir:
                errors = []
                if (error := self.__validate_human_flat(skill)) is not None:
                    errors.append(error)
                if (error := self.__validate_human_dir(skill)) is not None:
                    errors.append(error)
                if len(errors) > 0:
                    results[skill] = ValidationResult(errors)
            else:
                raise ValueError(f"Unknown skill format {skill.format}")
        return results
                    
    def __validate_human_dir(self,skill:Skill)->Optional[ValidationError]:
        folder_name = skill.folder_path.name
        if not folder_name.endswith(".skill"):
            return ValidationError(
                "Skill folder name doesn't ends on '.skill'",
                ValidationSeverity.ERROR
            )
            
        skill_name = folder_name[:-6]
        if skill_name != skill.properties.name:
            return ValidationError(
                "Skill folder name ({folder_name}) != skill name in header properties ({skill_name})",
                ValidationSeverity.ERROR,
                {
                    "folder_name": skill.folder_path.name,
                    "skill_name": skill.properties.name
                }
            )
            
    def __validate_human_flat(self,skill:Skill)->Optional[ValidationError]:
        file_name = skill.file_path.name
        if not file_name.endswith(".skill.md"):
            return ValidationError(
                "Skill file name doesn't ends on '.skill.md'",
                ValidationSeverity.ERROR
            )
            
        skill_name = file_name[:-9]
        if skill_name != skill.properties.name:
            return ValidationError(
                "Skill file name ({file_name}) != skill name in header properties ({skill_name})",
                ValidationSeverity.ERROR,
                {
                    "file_name": skill.file_path.name,
                    "skill_name": skill.properties.name
                }
            )
            
    def __validate_agent(self, skill: Skill) -> Optional[ValidationError]:
        if skill.folder_path.name != skill.properties.name:
            return ValidationError(
                "Folder name ({folder_name}) != skill name in header properties ({skill_name})",
                ValidationSeverity.ERROR,
                {
                    "folder_name": skill.folder_path.name,
                    "skill_name": skill.properties.name
                }
            )