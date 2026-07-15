"""Local filesystem skill source.

Локальный файловый источник навыков.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .source import ScanLocation, Source

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LocalSource(Source):
    """Skills discovered from one or more local files or directories.

    Навыки, обнаруженные в одном или нескольких локальных файлах или
    директориях.

    Attributes:
        scan_paths: Local paths to files or directories containing skills.
            Локальные пути к файлам или директориям, содержащим навыки.
        repo_path: Optional absolute path to the repository root. When omitted,
            each scan path defaults to its own repository root: the directory
            itself, or its parent when the scan path is a file.
            Опциональный абсолютный путь к корню репозитория. Если не указан,
            каждый путь сканирования сам становится своим корнем репозитория,
            либо используется его родительская директория, если путь
            сканирования является файлом.
    """

    scan_paths: Tuple[Path, ...]
    #: Local paths to files or directories containing skills.
    #: Локальные пути к файлам или директориям, содержащим навыки.

    repo_path: Optional[Path] = None
    #: Optional repository root used for repo_absolute link resolution.
    #: Опциональный корень репозитория для разрешения ссылок repo_absolute.

    original_repo_path: Optional[Path] = None
    #: Optional original repository root from the source skill, used when a
    #: copied skill is scanned from a different root (e.g. a target directory)
    #: so that repo-absolute links authored in the source still resolve.
    #: Опциональный исходный корень репозитория из исходного скилла,
    #: используется при сканировании скопированного скилла из другого корня,
    #: чтобы repo-absolute ссылки, созданные в источнике, продолжали разрешаться.

    tags: Tuple[str, ...] = ()
    #: Tag filter expressions applied to skills from this source.
    #: Выражения-фильтры тегов, применяемые к навыкам из этого источника.

    skip_folder: Tuple[str, ...] = ("examples",)
    #: Directory names inside a directory skill that are ignored when checking
    #: for nested skills. The directories are still copied as part of the skill.
    #: Имена директорий внутри директориального навыка, которые игнорируются при
    #: проверке на вложенные навыки. Сами директории всё равно копируются
    #: вместе с навыком.

    def __str__(self) -> str:
        return ", ".join(str(p) for p in self.scan_paths)

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
        paths = [p.as_posix() for p in self.scan_paths]
        result: Dict[str, Any] = {
            "type": self.source_type,
            "path": paths[0] if len(paths) == 1 else paths,
        }
        if self.repo_path is not None:
            result["repo_path"] = self.repo_path.as_posix()
        if self.original_repo_path is not None:
            result["original_repo_path"] = self.original_repo_path.as_posix()
        if self.tags:
            result["tags"] = list(self.tags)
        if self.skip_folder:
            result["skip_folder"] = list(self.skip_folder)
        return result

    def get_scan_locations(self) -> List[ScanLocation]:
        """Return the local filesystem scan locations.

        Вернуть локальные файловые локации для сканирования.

        Each scan path is used exactly as given: a file is scanned as a
        single file, and a directory is scanned recursively. The repository
        root defaults to the scan directory, or to the parent directory when
        the scan path is a file, unless an explicit ``repo_path`` was
        provided.

        Каждый путь сканирования используется точно как указан: файл
        сканируется как отдельный файл, директория — рекурсивно. Корень
        репозитория по умолчанию совпадает с директорией сканирования, либо
        с родительской директорией, если путь сканирования является файлом,
        если не задан явный ``repo_path``.
        """
        locations: List[ScanLocation] = []
        for path in self.scan_paths:
            scan_path = path.resolve()
            repo_path = (
                self.repo_path.resolve()
                if self.repo_path
                else (scan_path.parent if scan_path.is_file() else scan_path)
            )
            logger.debug(
                "LocalSource resolved: scan_path=%s repo_path=%s",
                scan_path,
                repo_path,
            )
            locations.append(ScanLocation(repo_path=repo_path, scan_path=scan_path))
        return locations
