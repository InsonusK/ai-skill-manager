"""Severity levels for validation results.

Уровни серьёзности результатов валидации.
"""

from enum import Enum


class ValidationSeverity(str, Enum):
    """Enumeration of possible validation severity values.

    Inherits from ``str`` so that members serialize directly to their
    string values.

    Перечисление возможных значений уровня серьёзности валидации.

    Наследуется от ``str``, поэтому члены сериализуются напрямую в свои
    строковые значения.
    """

    ERROR = "error"
    """Validation failed. / Валидация не пройдена."""

    WARNING = "warning"
    """Non-blocking issue. / Неблокирующая проблема."""

    SUCCESS = "success"
    """Validation passed. / Валидация пройдена."""
