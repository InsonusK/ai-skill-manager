"""Validation service.

High-level helpers that run the validator over skills.

Сервис валидации.
Высокоуровневые помощники, запускающие валидатор над навыками.
"""

from typing import List, Optional, Sequence

from .discover import discover
from ..entities import Skill, Source
from ..progress import ProgressCallback
from ..validators import Validator, ValidationReport


def validate(
    skills: List[Skill],
    progress: Optional[ProgressCallback] = None,
) -> ValidationReport:
    """Validate a list of already discovered skills.

    Проверяет список уже обнаруженных навыков.

    Args:
        skills: Skills to validate. / Навыки для валидации.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        Validation report containing all collected issues. /
            Отчёт о валидации, содержащий все собранные проблемы.
    """
    validator = Validator()
    return validator.validate(skills, progress=progress)


def run_validation(
    sources: Sequence[Source],
    progress: Optional[ProgressCallback] = None,
) -> ValidationReport:
    """Discover skills from sources and validate them.

    Обнаруживает навыки из источников и проверяет их.

    Args:
        sources: Skill sources to scan. / Источники навыков для сканирования.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        Validation report containing all collected issues. /
            Отчёт о валидации, содержащий все собранные проблемы.
    """
    skills = discover(sources, progress=progress)
    return validate(skills, progress=progress)
