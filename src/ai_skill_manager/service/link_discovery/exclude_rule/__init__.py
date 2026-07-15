"""Link validation exclude rules.

Правила исключения ссылок из валидации.
"""

from typing import List, Optional

from ....validation_settings import ValidationSettings
from .abs_exclude_rule import absExcludeRule
from .inline_code_exclude_rule import InlineCodeExcludeRule
from .skip_folder_exclude_rule import SkipFolderExcludeRule
from .web_link_exclude_rule import WebLinkExcludeRule


def build_link_exclude_rules(
    settings: Optional[ValidationSettings] = None,
) -> List[absExcludeRule]:
    """Build the default list of link exclude rules.

    Args:
        settings: Optional validation settings. When ``None``, defaults are used.
            / Опциональные настройки валидации. При ``None`` используются
            значения по умолчанию.

    Returns:
        List of exclude rules applied before link validation/adaptation.
            / Список правил исключения, применяемых перед валидацией/адаптацией
            ссылок.
    """
    skip_folders = settings.link_skip_folders if settings is not None else None
    return [
        InlineCodeExcludeRule(),
        WebLinkExcludeRule(),
        SkipFolderExcludeRule(skip_folders=skip_folders),
    ]


__all__ = [
    "absExcludeRule",
    "build_link_exclude_rules",
    "InlineCodeExcludeRule",
    "SkipFolderExcludeRule",
    "WebLinkExcludeRule",
]
