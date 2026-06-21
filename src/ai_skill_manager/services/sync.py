from typing import Sequence

from .discover import discover
from ..validators import Validator,ValidationFailedError
from ..models import Source

def run_sync(sources: Sequence[Source]) -> dict:
    skills = discover(sources)
    
    validator = Validator()
    validation_report = validator.validate(skills)
    if validation_report.has_errors:
        raise ValidationFailedError(validation_report)
    
    