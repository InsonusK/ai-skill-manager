"""Built-in validation rules.

Exports the default list of rules applied by ``Validator`` and the
abstract base class for implementing custom rules.

Встроенные правила валидации.

Экспортирует список правил по умолчанию, применяемых ``Validator``,
и абстрактный базовый класс для реализации собственных правил.
"""

from typing import List

from .abs_validation_rule import absValidationRule
from .link_validation_rule import LinkValidationRule
from .name_validator import NameValidationRule

# Default rule set used by Validator when no custom rules are supplied.
# Набор правил по умолчанию, используемый Validator, если не переданы кастомные правила.
DEFAULT_RULES: List[absValidationRule] = [NameValidationRule(), LinkValidationRule()]

__all__ = ["absValidationRule", "DEFAULT_RULES", "LinkValidationRule", "NameValidationRule"]
