"""GitHub skill source.

Источник навыков из GitHub.
"""

import logging
import re
import shutil
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from typing import Any, Dict, List, Optional, Tuple

from .source import ScanLocation, Source

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


# URL patterns for parsing GitHub repository URLs.
# Паттерны URL для разбора адресов репозиториев GitHub.
_GITHUB_URL_PATTERNS = [
    # https://github.com/owner/repo.git
    re.compile(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"),
    # git@github.com:owner/repo.git
    re.compile(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?/?$"),
]


def _parse_github_url(url: str) -> tuple:
    """Extract (owner, repo) from a GitHub URL.

    Извлечь (owner, repo) из URL GitHub.

    Args:
        url: GitHub repository URL. / URL репозитория GitHub.

    Returns:
        Tuple of (owner, repo). / Кортеж (owner, repo).

    Raises:
        ValueError: If the URL does not match a supported pattern.
        ValueError: Если URL не соответствует поддерживаемому паттерну.
    """
    for pattern in _GITHUB_URL_PATTERNS:
        match = pattern.match(url)
        if match:
            return match.group(1), match.group(2)
    raise ValueError(f"Invalid GitHub repository URL: {url}")


def _download_archive(owner: str, repo: str, tree: str) -> Path:
    """Download repo archive tarball to a temp file.

    Скачать архив репозитория в временный файл.

    Args:
        owner: Repository owner. / Владелец репозитория.
        repo: Repository name. / Имя репозитория.
        tree: Branch or tag name. / Имя ветки или тега.

    Returns:
        Path to the downloaded archive. / Путь к скачанному архиву.
    """
    archive_url = f"https://github.com/{owner}/{repo}/archive/{tree}.tar.gz"
    fd, tmp_path = tempfile.mkstemp(suffix=".tar.gz")
    try:
        with urllib.request.urlopen(archive_url, timeout=60) as response:
            with open(fd, "wb") as f:
                shutil.copyfileobj(response, f)
    except Exception:
        # Clean up the temp file on error to avoid leaving garbage behind.
        # Удаляем временный файл при ошибке, чтобы не оставлять мусор.
        Path(tmp_path).unlink(missing_ok=True)
        raise
    return Path(tmp_path)


def _extract_archive(archive_path: Path, extract_to: Path) -> None:
    """Extract a tar.gz archive.

    Распаковать архив tar.gz.

    Args:
        archive_path: Path to the archive. / Путь к архиву.
        extract_to: Destination directory. / Целевая директория.
    """
    with tarfile.open(archive_path, "r:gz") as tar:
        # filter available in Python 3.12+; suppresses deprecation warning.
        # filter доступен в Python 3.12+; подавляет предупреждение об устаревании.
        kwargs = {"filter": "fully_trusted"} if hasattr(tarfile, "data_filter") else {}
        tar.extractall(path=extract_to, **kwargs)


def _find_extracted_root(extract_to: Path) -> Path:
    """Find the single top-level directory created by GitHub archive extraction.

    Найти единственную директорию верхнего уровня, созданную при распаковке архива GitHub.

    Args:
        extract_to: Directory where the archive was extracted. /
            Директория, куда был распакован архив.

    Returns:
        Path to the repository root inside the extracted archive. /
            Путь к корню репозитория внутри распакованного архива.

    Raises:
        RuntimeError: If the archive does not contain exactly one top-level directory.
        RuntimeError: Если архив не содержит ровно одной директории верхнего уровня.
    """
    entries = [e for e in extract_to.iterdir() if e.is_dir()]
    if len(entries) != 1:
        raise RuntimeError(
            f"Expected exactly one top-level directory in extracted archive, found {len(entries)}"
        )
    return entries[0]


    
@dataclass(frozen=True)
class GitHubSource(Source):
    """Skills discovered from a GitHub repository.

    Навыки, обнаруженные в репозитории GitHub.

    Attributes:
        repo_url: GitHub repository URL. / URL репозитория GitHub.
        tree: Git tree, branch or tag to use. / Ветка, дерево или тег Git.
        subpath: Single subpath inside the repository to scan. Use multiple
            :class:`GitHubSource` instances to scan several subpaths.
            Один подпуть внутри репозитория для сканирования. Для сканирования
            нескольких подпутей используйте несколько экземпляров
            :class:`GitHubSource`.
    """
    class Context:
        scan_cache:Optional[ScanLocation] = None
        extracted_dirs:List[Path] = []
        
    repo_url: str
    #: GitHub repository URL. / URL репозитория GitHub.

    tree: str = "master"
    #: Git tree, branch or tag to use. / Ветка, дерево или тег Git.

    subpath: Optional[str] = None
    #: Subpath inside the repository to scan. / Подпуть внутри репозитория для сканирования.

    __context: Context = field(init=False, compare=False, hash=False, default_factory=Context)

    def __str__(self) -> str:
        parts = [self.repo_url, self.tree]
        if self.subpath:
            parts.append(self.subpath)
        return " ".join(parts)

    @property
    def source_type(self) -> str:
        """Return the source type identifier ``github``.

        Возвращает идентификатор типа источника ``github``.
        """
        return "github"

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable dictionary with source metadata.

        Возвращает сериализуемый словарь с метаданными источника.
        """
        result: Dict[str, Any] = {
            "type": self.source_type,
            "repo_url": self.repo_url,
            "tree": self.tree,
        }
        if self.subpath is not None:
            result["subpath"] = self.subpath
        return result

    def get_scan_location(self) -> ScanLocation:
        """Download, extract and return the repository scan location.

        Скачать, распаковать и вернуть локацию сканирования репозитория.

        The result is cached so repeated calls (for example from
        :class:`LinkWithContext`) do not download the archive again.
        The downloaded archive file is removed immediately; the extracted
        directory stays until :meth:`cleanup` is called.

        Результат кешируется, чтобы повторные вызовы (например, из
        :class:`LinkWithContext`) не скачивали архив заново. Скачанный
        архив удаляется сразу; распакованная директория остаётся до вызова
        :meth:`cleanup`.
        """
        if self.__context.scan_cache is not None:
            return self.__context.scan_cache

        owner, repo = _parse_github_url(self.repo_url)
        archive_path = _download_archive(owner, repo, self.tree)
        try:
            extracted_dir = Path(tempfile.mkdtemp())
            _extract_archive(archive_path, extracted_dir)
            self.__context.extracted_dirs.append(extracted_dir)

            repo_root = _find_extracted_root(extracted_dir)
            source_path = repo_root / self.subpath if self.subpath else repo_root
            if not source_path.exists():
                logger.error("subpath not found: %s", source_path)
                # Return a location that AutoDiscovery will treat as missing.
                # Возвращаем локацию, которую AutoDiscovery обработает как отсутствующую.
                loc = ScanLocation(repo_path=repo_root, source_path=source_path)
                self.__context.scan_cache = loc
                return loc
            loc = ScanLocation(repo_path=repo_root, source_path=source_path)
            self.__context.scan_cache = loc
            return loc
        finally:
            archive_path.unlink(missing_ok=True)

    def cleanup(self) -> None:
        """Remove extracted temporary directories and clear the scan cache.

        Удалить распакованные временные директории и очистить кеш сканирования.
        """
        self.__context.scan_cache = None
        for extracted_dir in self.__context.extracted_dirs:
            if extracted_dir.exists():
                shutil.rmtree(extracted_dir)
        self.__context.extracted_dirs = []
