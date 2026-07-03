"""Local filesystem skill source.

Локальный файловый источник навыков.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .source import ScanLocation, Source

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LocalSource(Source):
    """Skills discovered from a local file or directory.

    Навыки, обнаруженные в локальном файле или директории.

    Attributes:
        scan_path: Local path to a file or directory containing skills.
            Локальный путь к файлу или директории, содержащей навыки.
        repo_path: Optional absolute path to the repository root. When omitted,
            the directory containing ``path`` (or ``path`` itself if it is a
            directory) is used as the repository root for ``repo_absolute``
            link resolution.
            Опциональный абсолютный путь к корню репозитория. Если не указан,
            директория, содержащая ``path`` (или сам ``path``, если это
            директория), используется как корень репозитория для разрешения
            ссылок ``repo_absolute``.
    """

    scan_path: Path
    #: Local path to a file or directory containing skills.
    #: Локальный путь к файлу или директории, содержащей навыки.

    repo_path: Optional[Path] = None
    #: Optional repository root used for repo_absolute link resolution.
    #: Опциональный корень репозитория для разрешения ссылок repo_absolute.

    def __str__(self) -> str:
        return str(self.scan_path)

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
        result: Dict[str, Any] = {
            "type": self.source_type,
            "path": str(self.scan_path),
        }
        if self.repo_path is not None:
            result["repo_path"] = str(self.repo_path)
        return result

    def get_scan_location(self) -> ScanLocation:
        """Return the local filesystem scan location.

        Вернуть локальную файловую локацию для сканирования.

        If ``path`` points to a file, the scan directory is its parent.
        The repository root defaults to the scan directory unless an explicit
        ``repo_path`` was provided.

        Если ``path`` указывает на файл, директорией сканирования становится
        его родитель. Корень репозитория по умолчанию совпадает с директорией
        сканирования, если не задан явный ``repo_path``.
        """
        scan_path = self.scan_path.resolve()
        source_path = scan_path.parent if scan_path.is_file() else scan_path
        repo_path = self.repo_path.resolve() if self.repo_path else source_path
        logger.debug(
            "LocalSource resolved: scan_path=%s source_path=%s repo_path=%s",
            scan_path,
            source_path,
            repo_path,
        )
        return ScanLocation(repo_path=repo_path, source_path=source_path)
