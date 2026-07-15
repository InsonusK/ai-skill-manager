"""Web link model.

Модель веб-ссылки.
"""

from __future__ import annotations

from dataclasses import dataclass, InitVar
from typing import Optional

from .abs_link import absLink


@dataclass(frozen=True)
class WebLink(absLink):
    """A link that points to a web or mailto/ftp URI.

    Ссылка, указывающая на веб- или mailto/ftp URI.

    Attributes:
        url: The web address (URL) of the link.
            Веб-адрес (URL) ссылки.
    """

    url: str
