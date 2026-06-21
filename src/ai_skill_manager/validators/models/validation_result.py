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
    def has_erros(self)->bool:
        return any(
            er.severity == ValidationSeverity.ERROR
            for er in self.errors
        )
        
    @property
    def has_warnings(self)->bool:
        return any(
            er.severity == ValidationSeverity.WARNING
            for er in self.errors
        )