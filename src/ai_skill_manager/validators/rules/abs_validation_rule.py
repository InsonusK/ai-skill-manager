"""Abstract base class for validation rules.

Абстрактный базовый класс для правил валидации.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ...entities.skill import Skill
from ...progress import ProgressCallback
from ..models.validation_result import ValidationResult


class absValidationRule(ABC):
    """Base class that every validation rule must extend.

    Subclasses must implement ``validate`` and may override ``version``
    to provide rule versioning metadata.

    Базовый класс, который должен расширять каждое правило валидации.

    Подклассы должны реализовать ``validate`` и могут переопределить
    ``version`` для предоставления метаданных о версии правила.
    """

    @property
    def version(self) -> str:
        """Return the rule version string.

        Возвращает строку версии правила.
        """
        return ""

    @property
    def name(self) -> str:
        """Return the rule name, defaults to the class name.

        Возвращает имя правила; по умолчанию — имя класса.
        """
        return self.__class__.__name__

    @abstractmethod
    def validate(
        self,
        skills: List[Skill],
        progress: Optional[ProgressCallback] = None,
    ) -> Dict[Skill, ValidationResult]:
        """Validate a list of skills and return per-skill results.

        Проверяет список навыков и возвращает результаты по каждому навыку.

        Args:
            skills: Skills to validate.
                / Навыки для валидации.
            progress: Optional ``(stage, current, total)`` callback for progress
                reporting. / Опциональный callback для отчёта о прогрессе.

        Returns:
            Mapping from skill to its validation result.
                / Отображение навыка на его результат валидации.
        """
        ...
