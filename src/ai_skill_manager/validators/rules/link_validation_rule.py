"""Validation rule for links inside skills.

Правило валидации ссылок внутри скиллов.
"""

from pathlib import Path
from typing import Dict, List, Optional
from ...models import LinkWithContext
from ...entities import LinkKind, Skill, Link
from ..models import ValidationError, ValidationResult, ValidationSeverity
from .abs_validation_rule import absValidationRule


class LinkValidationRule(absValidationRule):
    """Validate that every link points to another skill or inside its own skill.

    Проверяет, что каждая ссылка ведёт либо на другой скилл, либо на файл
    внутри своей директории скилла.
    """

    def version(self) -> str:
        return "1.0.0"

    def validate(self, skills: List[Skill]) -> Dict[Skill, ValidationResult]:
        """Validate links for all provided skills.

        Валидирует ссылки для всех переданных скиллов.
        """
        results: Dict[Skill, ValidationResult] = {}
        for skill in skills:
            errors = self._validate_skill(skill, skills)
            if errors:
                results[skill] = ValidationResult(errors)
        return results

    def _validate_skill(self, skill: Skill, skills: List[Skill]) -> List[ValidationError]:
        """Validate all links inside ``skill``.

        Валидирует все ссылки внутри ``skill``.
        """
        errors: List[ValidationError] = []
        for skill_file in skill.files:
            for link in skill_file.links:
                link_context = LinkWithContext.build(skill, skill_file, link)

                if (error := self.__validate_link(link_context, skills)) is not None:
                    errors.append(error)
        return errors

    def __validate_link(self, link: LinkWithContext, skills: List[Skill]) -> Optional[ValidationError]:
        if link.kind == LinkKind.web:
            return None

        if link.os_absolute_path is None:
            return ValidationError(
                message="Link doesn't have absolute OS path: {link_raw}",
                severity=ValidationSeverity.ERROR,
                params={
                    "link_raw": link.raw
                },
            )

        if link.is_link_to_skill_file:
            return None
        
        if link.is_link_to_another_skill(skills) is not None:
            return None

        return ValidationError(
            message="Link {link_raw} doesn't lead to subfiles or other skills",
            severity=ValidationSeverity.ERROR,
            params={
                    "link_raw": link.raw
            },
        )
