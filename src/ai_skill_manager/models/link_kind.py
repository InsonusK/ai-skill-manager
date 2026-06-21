"""Link path kinds.

Типы путей ссылок.
"""

from enum import Enum


class LinkKind(Enum):
    """Whether a link target is an OS absolute, repo absolute or relative path.

    Является ли цель ссылки абсолютным путём ОС, абсолютным путём репозитория
    или относительным путём.
    """

    os_absolute = "os_absolute"
    """OS absolute path. / Абсолютный путь ОС."""

    relative = "relative"
    """Relative path. / Относительный путь."""

    repo_absolute = "repo_absolute"
    """Path from root of repository. / Путь от корня репозитория."""

    web = "relative"
    """Path to http links"""