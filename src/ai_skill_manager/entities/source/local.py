"""Local filesystem skill source.

Локальный файловый источник навыков.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from .source import Source


@dataclass(frozen=True)
class LocalSource(Source):
    """Skills discovered from a local file or directory.

    Навыки, обнаруженные в локальном файле или директории.
    """

    path: Path
    #: Local path to a file or directory containing skills.
    #: Локальный путь к файлу или директории, содержащей навыки.
    
    def __str__(self)->str:
        return str(self.path)
    
    @property
    def source_type(self) -> str:
        """Return the source type identifier ``local``.

        Возвращает идентификатор типа источника ``local``.
        """
        return "local"

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable dictionary with source metadata.

        Возвращает сериализуемый словарь с метаданными источника.
        """
        return {
            "type": self.source_type,
            "path": str(self.path),
        }
