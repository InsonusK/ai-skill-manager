from ai_skill_manager.validators.models.validation_severity import ValidationSeverity
from ai_skill_manager.validators.models.validation_result import ValidationErrorType


from dataclasses import dataclass
from typing import Any, Type


@dataclass(slots=True)
class ValidationResult:
    message: str
    severity: ValidationSeverity
    details: dict[str, Any] | None = None