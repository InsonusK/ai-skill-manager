"""Storage-level link models.

Модели ссылки на уровне хранения.
"""

from .abs_link import absLink
from .file_link import FileLink
from .link_data import LinkData
from .web_link import WebLink

__all__ = [
    "absLink",
    "FileLink",
    "LinkData",
    "WebLink",
]
