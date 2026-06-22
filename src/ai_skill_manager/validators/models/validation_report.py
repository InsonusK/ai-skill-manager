"""Aggregated validation report model.

Модель агрегированного отчёта валидации.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ...entities.skill import Skill
from ..rules import absValidationRule
from .validation_result import ValidationResult
from .validation_severity import ValidationSeverity


@dataclass(slots=True)
class ValidationReport:
    """Aggregates per-skill, per-rule validation results.

    Provides helpers to detect whether any errors exist and to extract
    only the errors from the full result map.

    Агрегирует результаты валидации по навыкам и правилам.

    Предоставляет вспомогательные методы для определения наличия ошибок
    и извлечения только ошибок из полной карты результатов.
    """

    result: Dict[Skill, Dict[absValidationRule, ValidationResult]] = field(default_factory=dict)
    """Nested map: skill -> rule -> result. / Вложенная карта: навык -> правило -> результат."""

    @property
    def has_errors(self) -> bool:
        """Return ``True`` if any rule reported an error for any skill.

        Возвращает ``True``, если хотя бы одно правило сообщило об ошибке
        для какого-либо навыка.
        """
        return any(
            vr.severity == ValidationSeverity.ERROR
            for skill_results in self.result.values()
            for vr in skill_results.values()
        )

    @property
    def errors(self) -> Dict[Skill, Dict[absValidationRule, ValidationResult]]:
        """Return a map containing only error-level results.

        Возвращает карту, содержащую только результаты уровня ERROR.
        """
        _return = {}
        for skill, rule_results in self.result.items():
            skill_errors = {}
            for rule, rule_result in rule_results.items():
                # Keep only results that include an error severity.
                # Оставляем только результаты с уровнем серьёзности ERROR.
                if rule_result.severity == ValidationSeverity.ERROR:
                    skill_errors[rule] = rule_result
            if len(skill_errors) > 0:
                _return[skill] = skill_errors
        return _return
