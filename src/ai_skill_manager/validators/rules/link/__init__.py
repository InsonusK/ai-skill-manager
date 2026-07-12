"""Link exclusion rules.

Used directly by ``LinkAdapter`` to skip inline-code, web and skip-folder
links when rewriting. Link *validity* is no longer checked separately: the
sync materialization pass is now the sole place a link is resolved, and it
resolves against the same source skill graph link validation used to check
against.

Правила исключения ссылок.

Используются напрямую ``LinkAdapter`` для пропуска ссылок в инлайн-коде,
веб-ссылок и ссылок из пропускаемых директорий при переписывании.
*Валидность* ссылки отдельно больше не проверяется: единственное место, где
ссылка теперь резолвится, - проход материализации sync, и он резолвит её
относительно того же графа исходных скиллов, с которым раньше сверялась
валидация ссылок.
"""

from .exclude_rule import (
    InlineCodeExcludeRule,
    SkipFolderExcludeRule,
    WebLinkExcludeRule,
    absExcludeRule,
    build_link_exclude_rules,
)

__all__ = [
    "absExcludeRule",
    "build_link_exclude_rules",
    "InlineCodeExcludeRule",
    "SkipFolderExcludeRule",
    "WebLinkExcludeRule",
]
