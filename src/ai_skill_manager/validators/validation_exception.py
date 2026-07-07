"""Exception raised when skill validation fails.

Исключение, возникающее при неудачной валидации навыка.
"""

from typing import List, Optional

from .models.validation_report import ValidationReport


class ValidationFailedError(Exception):
    """Raised when validation fails due to errors.

    Возникает, когда валидация не пройдена из-за наличия ошибок.
    """

    __slots__ = ("report", "skills")

    def __init__(self, report: ValidationReport, skills: Optional[List] = None):
        """Initialize the exception with the validation report.

        Args:
            report: Report containing validation errors.
                / Отчёт, содержащий ошибки валидации.
            skills: Skills that were discovered before validation failed.
                / Навыки, обнаруженные до неудачной валидации.
        """
        self.report = report
        self.skills = skills
        super().__init__("Validation failed with error(s)")

    @property
    def has_errors(self) -> bool:
        """Return ``True`` if the report contains any errors.

        Возвращает ``True``, если в отчёте есть хотя бы одна ошибка.
        """
        return self.report.has_errors
