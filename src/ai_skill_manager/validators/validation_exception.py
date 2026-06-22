"""Exception raised when skill validation fails.

Исключение, возникающее при неудачной валидации навыка.
"""

from .models.validation_report import ValidationReport


class ValidationFailedError(Exception):
    """Raised when validation fails due to errors.

    Возникает, когда валидация не пройдена из-за наличия ошибок.
    """

    __slots__ = ("report",)

    def __init__(self, report: ValidationReport):
        """Initialize the exception with the validation report.

        Args:
            report: Report containing validation errors.
                / Отчёт, содержащий ошибки валидации.
        """
        self.report = report
        super().__init__("Validation failed with error(s)")

    @property
    def has_errors(self) -> bool:
        """Return ``True`` if the report contains any errors.

        Возвращает ``True``, если в отчёте есть хотя бы одна ошибка.
        """
        return self.report.has_errors
