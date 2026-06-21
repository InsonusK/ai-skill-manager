from __future__ import annotations
from .validation_error import ValidationError
from .validation_severity import ValidationSeverity
from dataclasses import dataclass
from typing import List

@dataclass(slots=True)
class ValidationResult:
    errors: List[ValidationError]
    
    @staticmethod    
    def single(single_error:ValidationError)->ValidationResult:
        return ValidationResult([single_error])        
    
    @property
    def has_errors(self) -> bool:
        return any(
            er.severity == ValidationSeverity.ERROR
            for er in self.errors
        )

    @property
    def has_warnings(self) -> bool:
        return any(
            er.severity == ValidationSeverity.WARNING
            for er in self.errors
        )

    @property
    def severity(self) -> ValidationSeverity:
        """Return the aggregated severity for this result.

        Returns ``ERROR`` if any error is present, ``WARNING`` if only warnings
        are present, otherwise ``SUCCESS``.
        """
        if self.has_errors:
            return ValidationSeverity.ERROR
        if self.has_warnings:
            return ValidationSeverity.WARNING
        return ValidationSeverity.SUCCESS