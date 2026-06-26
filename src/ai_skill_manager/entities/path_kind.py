from enum import Enum


class PathKind(Enum):
    """Whether a raw link path is an OS absolute, repo absolute or relative path.

    Является ли исходный путь ссылки абсолютным путём ОС, абсолютным путём
    репозитория или относительным путём.
    """

    os_absolute = "os_absolute"
    """OS absolute path. / Абсолютный путь ОС."""

    relative = "relative"
    """Relative path. / Относительный путь."""

    repo_absolute = "repo_absolute"
    """Path from root of repository. / Путь от корня репозитория."""