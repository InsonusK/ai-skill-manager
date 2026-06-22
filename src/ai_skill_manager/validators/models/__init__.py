"""Validation data models.

Exports all data structures used to represent validation severity,
errors, results, and reports.

Модели данных валидации.

Экспортирует все структуры данных, используемые для представления
уровня серьёзности, ошибок, результатов и отчётов валидации.
"""

from .validation_severity import ValidationSeverity
from .validation_error import ValidationError
from .validation_result import ValidationResult
from .validation_report import ValidationReport

__all__ = [
    "ValidationSeverity",
    "ValidationError",
    "ValidationResult",
    "ValidationReport",
]
