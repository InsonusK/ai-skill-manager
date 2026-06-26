from .link_kind import LinkKind


from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LinkPath:
    """Processed path data for a link target.

    Обработанные данные пути для цели ссылки.

    Attributes:
        kind: Where the resolved link points.
            Куда ведёт разрешённая ссылка.
        formatted: Target path formatted for the link kind.
            Путь цели, приведённый к формату, соответствующему kind.
        repo_path: Path relative to the repository root.
            Путь относительно корня репозитория.
        os_path: Absolute OS path to the target.
            Абсолютный путь ОС к цели.
    """

    kind: LinkKind
    formatted: str
    repo_path: str
    os_path: Path