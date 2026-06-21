from .models.validation_report import ValidationReport

class ValidationFailedError(Exception):
    """Валидация не пройдена — есть ошибки."""
    
    __slots__ = ("report",)
    
    def __init__(self, report: ValidationReport):
        self.report = report
        super().__init__(f"Validation failed with error(s)")
    
    @property
    def has_errors(self) -> bool:
        return self.report.has_errors