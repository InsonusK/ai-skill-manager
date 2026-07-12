"""Built-in validation rules.

Exports the default list of rules applied by ``Validator`` and the
abstract base class for implementing custom rules.

Встроенные правила валидации.

Экспортирует список правил по умолчанию, применяемых ``Validator``,
и абстрактный базовый класс для реализации собственных правил.
"""

from typing import List

from .abs_validation_rule import absValidationRule
from .conflict_validation_rule import ConflictValidationRule
from .link import build_link_exclude_rules
from .name_validator import NameValidationRule

# Default rule set used by Validator when no custom rules are supplied.
# Link resolution is checked as part of sync's materialization pass, not
# here - see validators/rules/link/__init__.py.
# Набор правил по умолчанию, используемый Validator, если не переданы
# кастомные правила. Резолюция ссылок проверяется в рамках прохода
# материализации sync, а не здесь - см. validators/rules/link/__init__.py.
DEFAULT_RULES: List[absValidationRule] = [NameValidationRule(), ConflictValidationRule()]

__all__ = [
    "absValidationRule",
    "build_link_exclude_rules",
    "ConflictValidationRule",
    "DEFAULT_RULES",
    "NameValidationRule",
]
