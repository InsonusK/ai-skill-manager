"""Validation result model for a single skill-rule pair.

Модель результата валидации для одной пары навык-правило.
"""

from __future__ import annotations
from .validation_error import ValidationError
from .validation_severity import ValidationSeverity
from dataclasses import dataclass
from typing import List


@dataclass(slots=True)
class ValidationResult:
    """Holds a list of validation errors for one skill under one rule.

    Aggregates severity across errors to let callers quickly decide
    whether the result passed, warned, or failed.

    Содержит список ошибок валидации для одного навыка по одному правилу.

    Агрегирует серьёзность ошибок, позволяя вызывающим сторонам быстро
    определить, прошёл ли результат, выдал предупреждение или ошибку.
    """

    errors: List[ValidationError]
    """Validation errors found for the skill. / Ошибки валидации, найденные для навыка."""

    @staticmethod
    def single(single_error: ValidationError) -> ValidationResult:
        """Create a result containing exactly one error.

        Создаёт результат, содержащий ровно одну ошибку.

        Args:
            single_error: The single validation error.
                / Единственная ошибка валидации.

        Returns:
            Validation result wrapping the error.
                / Результат валидации, оборачивающий ошибку.
        """
        return ValidationResult([single_error])

    @property
    def has_errors(self) -> bool:
        """Return ``True`` if any error has ERROR severity.

        Возвращает ``True``, если хотя бы одна ошибка имеет уровень ERROR.
        """
        return any(
            er.severity == ValidationSeverity.ERROR
            for er in self.errors
        )

    @property
    def has_warnings(self) -> bool:
        """Return ``True`` if any error has WARNING severity.

        Возвращает ``True``, если хотя бы одна ошибка имеет уровень WARNING.
        """
        return any(
            er.severity == ValidationSeverity.WARNING
            for er in self.errors
        )

    @property
    def severity(self) -> ValidationSeverity:
        """Return the aggregated severity for this result.

        Returns ``ERROR`` if any error is present, ``WARNING`` if only warnings
        are present, otherwise ``SUCCESS``.

        Возвращает агрегированный уровень серьёзности для этого результата.

        Возвращает ``ERROR``, если присутствует ошибка, ``WARNING``, если
        только предупреждения, иначе ``SUCCESS``.
        """
        if self.has_errors:
            return ValidationSeverity.ERROR
        if self.has_warnings:
            return ValidationSeverity.WARNING
        return ValidationSeverity.SUCCESS
