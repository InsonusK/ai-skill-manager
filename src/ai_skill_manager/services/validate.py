from typing import Optional, Sequence

from .discover import discover
from ..validators import Validator, ValidationReport
from ..entities import Source


def run_validation(sources: Sequence[Source]) -> ValidationReport:
    skills = discover(sources)

    validator = Validator()
    return validator.validate(skills)
