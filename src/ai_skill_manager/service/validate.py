"""Validation service.

High-level helpers that run the validator over skills.

Сервис валидации.
Высокоуровневые помощники, запускающие валидатор над навыками.
"""

from typing import List, Optional, Sequence

from .discover import discover
from ..validation_settings import ValidationSettings
from ..entities import Skill, Source
from ..progress import ProgressCallback
from ..validators import Validator, ValidationReport
from ..validators.rules import build_default_rules


def validate(
    skills: List[Skill],
    settings: Optional[ValidationSettings] = None,
    progress: Optional[ProgressCallback] = None,
) -> ValidationReport:
    """Validate a list of already discovered skills.

    Проверяет список уже обнаруженных навыков.

    Args:
        skills: Skills to validate. / Навыки для валидации.
        settings: Optional validation settings.
            / Опциональные настройки валидации.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        Validation report containing all collected issues. /
            Отчёт о валидации, содержащий все собранные проблемы.
    """
    validator = Validator(build_default_rules(settings))
    return validator.validate(skills, progress=progress)


def run_validation(
    sources: Sequence[Source],
    settings: Optional[ValidationSettings] = None,
    progress: Optional[ProgressCallback] = None,
) -> ValidationReport:
    """Discover skills from sources and validate them.

    Обнаруживает навыки из источников и проверяет их.

    Args:
        sources: Skill sources to scan. / Источники навыков для сканирования.
        settings: Optional validation settings.
            / Опциональные настройки валидации.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        Validation report containing all collected issues. /
            Отчёт о валидации, содержащий все собранные проблемы.
    """
    skills = discover(sources, progress=progress)
    return validate(skills, settings=settings, progress=progress)
