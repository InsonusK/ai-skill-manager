from typing import List

from .abs_validation_rule import absValidationRule
from .link_validation_rule import LinkValidationRule
from .name_validator import NameValidationRule

DEFAULT_RULES: List[absValidationRule] = [NameValidationRule(), LinkValidationRule()]
