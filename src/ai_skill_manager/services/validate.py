"""Validation service.

High-level helper that discovers skills from the given sources and runs
the validator over them.

Сервис валидации.
Высокоуровневый помощник, который обнаруживает навыки из заданных источников
и запускает валидатор.
"""

from typing import Optional, Sequence

from .discover import discover
from ..validators import Validator, ValidationReport
from ..entities import Source


def run_validation(sources: Sequence[Source]) -> ValidationReport:
    """Discover skills from sources and validate them.

    Discover skills from sources and validate them.

    Обнаружить навыки из источников и провалидировать их.

    Args:
        sources: Skill sources to scan. / Источники навыков для сканирования.

    Returns:
        Validation report containing all collected issues. /
        Отчёт о валидации, содержащий все собранные проблемы.
    """
    # Discover skills before validating them.
    # Сначала обнаруживаем навыки, затем валидируем.
    skills = discover(sources)

    validator = Validator()
    return validator.validate(skills)
