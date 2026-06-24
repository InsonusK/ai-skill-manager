"""Web link model.

Модель веб-ссылки.
"""

from __future__ import annotations

from dataclasses import dataclass, InitVar
from typing import Optional

from .absLink import absLink


@dataclass(frozen=True)
class WebLink(absLink):
    """A link that points to a web or mailto/ftp URI.

    Ссылка, указывающая на веб- или mailto/ftp URI.

    Attributes:
        path: The web address (URL) of the link.
            Веб-адрес (URL) ссылки.
    """

    path: str
    header_value: InitVar[Optional[str]] = None
    is_image_value: InitVar[bool] = False

    def __post_init__(self, header_value: Optional[str], is_image_value: bool) -> None:
        """Store the common header and image flags.

        Сохранить общие флаги заголовка и изображения.
        """
        object.__setattr__(self, "header", header_value)
        object.__setattr__(self, "is_image", is_image_value)

    @property
    def target(self) -> str:
        """Return the URL target.

        Вернуть целевой URL.
        """
        return self.path
