"""Public API for skill validation.

Exports the main ``Validator`` class and the ``ValidationReport`` model
that aggregates all validation results.

Публичный API для валидации навыков.

Экспортирует основной класс ``Validator`` и модель ``ValidationReport``,
которая агрегирует все результаты валидации.
"""

# Import the main validator entry point.
# Импортируем основную точку входа валидатора.
from .validator import Validator

# Import the model that contains per-skill validation results.
# Импортируем модель, содержащую результаты валидации по каждому навыку.
from .models import ValidationReport

__all__ = ["Validator", "ValidationReport"]
