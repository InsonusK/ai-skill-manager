"""Public API for skill validation.

Exports the main ``Validator`` class, the ``ValidationFailedError``
exception, and the ``ValidationReport`` model that aggregates all
validation results.

Публичный API для валидации навыков.

Экспортирует основной класс ``Validator``, исключение
``ValidationFailedError`` и модель ``ValidationReport``,
которая агрегирует все результаты валидации.
"""

# Import the main validator entry point.
# Импортируем основную точку входа валидатора.
from .validator import Validator

# Import the exception raised when validation fails.
# Импортируем исключение, возникающее при неудачной валидации.
from .validation_exception import ValidationFailedError

# Import the model that contains per-skill validation results.
# Импортируем модель, содержащую результаты валидации по каждому навыку.
from .models import ValidationReport

__all__ = ["Validator", "ValidationFailedError", "ValidationReport"]
