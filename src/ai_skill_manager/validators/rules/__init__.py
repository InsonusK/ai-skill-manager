"""Built-in validation rules.

Exports the default list of rules applied by ``Validator`` and the
abstract base class for implementing custom rules.

Встроенные правила валидации.

Экспортирует список правил по умолчанию, применяемых ``Validator``,
и абстрактный базовый класс для реализации собственных правил.
"""

from typing import List, Optional

from ...validation_settings import ValidationSettings
from .abs_validation_rule import absValidationRule
from .conflict_validation_rule import ConflictValidationRule
from .link import LinkValidationRule, build_link_exclude_rules
from .name_validator import NameValidationRule


def build_default_rules(
    settings: Optional[ValidationSettings] = None,
) -> List[absValidationRule]:
    """Build the default rule list, optionally using validation settings.

    Args:
        settings: Optional validation settings used to configure rules that
            support them.
            / Опциональные настройки валидации для конфигурации поддерживающих
            их правил.

    Returns:
        Default validation rules.
            / Правила валидации по умолчанию.
    """
    return [
        NameValidationRule(),
        ConflictValidationRule(),
        LinkValidationRule(exclude_rules=build_link_exclude_rules(settings)),
    ]


# Default rule set used by Validator when no custom rules are supplied.
# Набор правил по умолчанию, используемый Validator, если не переданы кастомные правила.
DEFAULT_RULES: List[absValidationRule] = build_default_rules()

__all__ = [
    "absValidationRule",
    "build_default_rules",
    "ConflictValidationRule",
    "DEFAULT_RULES",
    "LinkValidationRule",
    "NameValidationRule",
]
