"""Validation rule that detects skills with duplicate names.

Duplicate skill names are always reported as errors because they would
overwrite each other during synchronization.

Правило валидации, обнаруживающее навыки с повторяющимися именами.
Конфликты имён всегда сообщаются как ошибки, поскольку при синхронизации
они перезаписали бы друг друга.
"""

from typing import Dict, List, Optional

from .abs_validation_rule import Skill, absValidationRule, List
from ...progress import ProgressCallback
from ..models import ValidationError, ValidationResult, ValidationSeverity


class ConflictValidationRule(absValidationRule):
    """Detect duplicate skill names across all discovered skills."""

    @property
    def version(self) -> str:
        """Return the rule version. / Возвращает версию правила."""
        return "1.0.0"

    def validate(
        self,
        skills: List[Skill],
        progress: Optional[ProgressCallback] = None,
    ) -> Dict[Skill, ValidationResult]:
        """Find every skill name that is declared by more than one skill.

        Находит каждое имя навыка, которое объявлено более чем одним навыком.

        Args:
            skills: Skills to validate. / Навыки для валидации.
            progress: Optional ``(stage, current, total)`` callback for progress
                reporting. / Опциональный callback для отчёта о прогрессе.

        Returns:
            Mapping from each conflicting skill to its error result.
                / Отображение каждого конфликтующего навыка на результат с ошибкой.
        """
        by_name: Dict[str, List[Skill]] = {}
        for skill in skills:
            name = skill.properties.name
            if name is None:
                continue
            by_name.setdefault(name, []).append(skill)

        results: Dict[Skill, ValidationResult] = {}
        for name, named_skills in by_name.items():
            if len(named_skills) < 2:
                continue

            paths = "\n".join(f"  - {s.file_path}" for s in named_skills)
            error = ValidationError(
                message="Skill name '{name}' is used by {count} skills:\n{paths}",
                severity=ValidationSeverity.ERROR,
                params={
                    "name": name,
                    "count": len(named_skills),
                    "paths": paths,
                },
            )
            result = ValidationResult.single(error)
            for skill in named_skills:
                results[skill] = result

        return results
