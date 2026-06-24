"""Validation service.

High-level helpers that run the validator over skills.

Сервис валидации.
Высокоуровневые помощники, запускающие валидатор над навыками.
"""

from typing import List, Sequence

from .discover import discover
from ..entities import Skill, Source
from ..validators import Validator, ValidationReport


def validate(skills: List[Skill]) -> ValidationReport:
    """Validate a list of already discovered skills.

    Проверяет список уже обнаруженных навыков.

    Args:
        skills: Skills to validate. / Навыки для валидации.

    Returns:
        Validation report containing all collected issues. /
            Отчёт о валидации, содержащий все собранные проблемы.
    """
    validator = Validator()
    return validator.validate(skills)


def run_validation(sources: Sequence[Source]) -> ValidationReport:
    """Discover skills from sources and validate them.

    Обнаруживает навыки из источников и проверяет их.

    Args:
        sources: Skill sources to scan. / Источники навыков для сканирования.

    Returns:
        Validation report containing all collected issues. /
            Отчёт о валидации, содержащий все собранные проблемы.
    """
    skills = discover(sources)
    return validate(skills)
