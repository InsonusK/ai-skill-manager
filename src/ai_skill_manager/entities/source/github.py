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
            owner, repo = match.group(1), match.group(2)
            logger.debug("Parsed GitHub URL: owner=%s repo=%s", owner, repo)
            return owner, repo
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
    logger.debug("Downloading GitHub archive: %s", archive_url)
    fd, tmp_path = tempfile.mkstemp(suffix=".tar.gz")
    try:
        with urllib.request.urlopen(archive_url, timeout=60) as response:
            with open(fd, "wb") as f:
                shutil.copyfileobj(response, f)
        logger.debug("Downloaded archive to %s", tmp_path)
    except Exception:
        # Clean up the temp file on error to avoid leaving garbage behind.
        # Удаляем временный файл при ошибке, чтобы не оставлять мусор.
        Path(tmp_path).unlink(missing_ok=True)
        raise
    return Path(tmp_path)


def _extract_archive(archive_path: Path, extract_to: Path) -> None:
    logger.debug("Extracting archive %s to %s", archive_path, extract_to)
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
    logger.debug("Extracted archive root entries: %d", len(entries))
    if len(entries) != 1:
        raise RuntimeError(
            f"Expected exactly one top-level directory in extracted archive, found {len(entries)}"
        )
    logger.debug("Archive root: %s", entries[0])
    return entries[0]


    
@dataclass(frozen=True)
class GitHubSource(Source):
    """Skills discovered from a GitHub repository.

    Навыки, обнаруженные в репозитории GitHub.

    Attributes:
        repo_url: GitHub repository URL. / URL репозитория GitHub.
        tree: Git tree, branch or tag to use. / Ветка, дерево или тег Git.
        subpaths: Subpaths inside the repository to scan. The repository is
            downloaded and extracted once and reused for every subpath.
            Подпути внутри репозитория для сканирования. Репозиторий
            скачивается и распаковывается один раз и переиспользуется для
            каждого подпути.
    """
    class Context:
        scan_cache: Optional[List[ScanLocation]] = None
        extracted_dirs:List[Path] = []

    repo_url: str
    #: GitHub repository URL. / URL репозитория GitHub.

    tree: str = "master"
    #: Git tree, branch or tag to use. / Ветка, дерево или тег Git.

    subpaths: Tuple[Optional[str], ...] = (None,)
    #: Subpaths inside the repository to scan. / Подпути внутри репозитория для сканирования.

    tags: Tuple[str, ...] = ()
    #: Tag filter expressions applied to skills from this source.
    #: Выражения-фильтры тегов, применяемые к навыкам из этого источника.

    skip_folder: Tuple[str, ...] = ("examples",)
    #: Directory names inside a directory skill that are ignored when checking
    #: for nested skills. The directories are still copied as part of the skill.
    #: Имена директорий внутри директориального навыка, которые игнорируются при
    #: проверке на вложенные навыки. Сами директории всё равно копируются
    #: вместе с навыком.

    __context: Context = field(init=False, compare=False, hash=False, default_factory=Context)

    def __str__(self) -> str:
        parts = [self.repo_url, self.tree]
        named_subpaths = [sp for sp in self.subpaths if sp]
        if named_subpaths:
            parts.append(",".join(named_subpaths))
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
        named_subpaths = [sp for sp in self.subpaths if sp is not None]
        if named_subpaths:
            result["subpath"] = named_subpaths[0] if len(named_subpaths) == 1 else named_subpaths
        if self.tags:
            result["tags"] = list(self.tags)
        if self.skip_folder:
            result["skip_folder"] = list(self.skip_folder)
        return result

    def get_scan_locations(self) -> List[ScanLocation]:
        """Download, extract once and return a scan location per subpath.

        Скачать, распаковать один раз и вернуть локацию сканирования для
        каждого подпути.

        The result is cached so repeated calls (for example from
        :class:`LinkWithContext`) do not download the archive again. The
        archive is downloaded and extracted a single time regardless of how
        many subpaths are configured. The downloaded archive file is removed
        immediately; the extracted directory stays until :meth:`cleanup` is
        called.

        Результат кешируется, чтобы повторные вызовы (например, из
        :class:`LinkWithContext`) не скачивали архив заново. Архив
        скачивается и распаковывается один раз независимо от количества
        настроенных подпутей. Скачанный архив удаляется сразу; распакованная
        директория остаётся до вызова :meth:`cleanup`.
        """
        if self.__context.scan_cache is not None:
            logger.debug("Using cached GitHub scan locations for %s", self.repo_url)
            return self.__context.scan_cache

        logger.debug("Resolving GitHub source: %s tree=%s subpaths=%s", self.repo_url, self.tree, self.subpaths)
        owner, repo = _parse_github_url(self.repo_url)
        archive_path = _download_archive(owner, repo, self.tree)
        try:
            extracted_dir = Path(tempfile.mkdtemp())
            _extract_archive(archive_path, extracted_dir)
            self.__context.extracted_dirs.append(extracted_dir)

            repo_root = _find_extracted_root(extracted_dir)
            locations: List[ScanLocation] = []
            for subpath in self.subpaths:
                source_path = repo_root / subpath if subpath else repo_root
                logger.debug("GitHub scan location: repo_root=%s source_path=%s", repo_root, source_path)
                if not source_path.exists():
                    # AutoDiscovery treats a missing scan path as an empty result.
                    # AutoDiscovery обрабатывает отсутствующий путь сканирования как пустой результат.
                    logger.error("subpath not found: %s", source_path)
                locations.append(ScanLocation(repo_path=repo_root, scan_path=source_path))
            self.__context.scan_cache = locations
            return locations
        finally:
            archive_path.unlink(missing_ok=True)

    def cleanup(self) -> None:
        """Remove extracted temporary directories and clear the scan cache.

        Удалить распакованные временные директории и очистить кеш сканирования.
        """
        logger.debug("Cleaning up GitHub source temporary directories")
        self.__context.scan_cache = None
        for extracted_dir in self.__context.extracted_dirs:
            if extracted_dir.exists():
                logger.debug("Removing extracted directory: %s", extracted_dir)
                shutil.rmtree(extracted_dir)
        self.__context.extracted_dirs = []
