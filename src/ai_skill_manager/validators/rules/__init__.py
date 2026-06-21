from typing import List

from .abs_validation_rule import absValidationRule
from .name_validator import NameValidationRule

DEFAULT_RULES:List[absValidationRule] = [NameValidationRule()]