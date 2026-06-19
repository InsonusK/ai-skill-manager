"""GitHub source discovery strategy.

Downloads a GitHub repository archive, extracts it to a temp directory,
and discovers skills from one or more subpaths using :class:`AutoDiscovery`.

Стратегия обнаружения из источника GitHub.
Скачивает архив репозитория GitHub, распаковывает его во временную директорию
и обнаруживает навыки в одном или нескольких подпутях с помощью :class:`AutoDiscovery`.
"""

import logging
import re
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import List, Optional, Union

from ...models import Skill
from ...models.source import GitHubSource
from .auto import AutoDiscovery
from .DiscoveryStrategy import DiscoveryStrategy

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
        RuntimeError: Если архив не содержит ровно одну директорию верхнего уровня.
    """
    entries = [e for e in extract_to.iterdir() if e.is_dir()]
    if len(entries) != 1:
        raise RuntimeError(
            f"Expected exactly one top-level directory in extracted archive, found {len(entries)}"
        )
    return entries[0]


class GitHubDiscovery(DiscoveryStrategy):
    """Discover skills from a GitHub repository.

    Downloads the repo archive for the specified tree/branch, extracts it,
    and discovers skills from the configured subpaths using :class:`AutoDiscovery`.

    Обнаруживает навыки из репозитория GitHub.
    Скачивает архив репозитория для указанного tree/branch, распаковывает его
    и обнаруживает навыки в настроенных подпутях с помощью :class:`AutoDiscovery`.
    """

    def __init__(
        self,
        source_path,
        tree: str = "master",
        subpath: Union[str, List[str]] = "skills",
    ):
        """Initialize with a GitHub repo URL and optional tree/subpath.

        Инициализировать URL репозитория GitHub и опциональными tree/subpath.

        Args:
            source_path: GitHub repository URL. / URL репозитория GitHub.
            tree: Branch or tag to download (default: ``master``). /
                Ветка или тег для скачивания (по умолчанию: ``master``).
            subpath: Path or list of paths inside the repo to scan. /
                Путь или список путей внутри репозитория для сканирования.
        """
        # source_path is the repo URL (str or Path-like); avoid base resolve().
        # source_path — URL репозитория (str или Path-like); избегаем base resolve().
        self.repo_url = str(source_path)
        self.tree = tree
        self.subpath = subpath
        self._extracted_dir: Optional[Path] = None
        # Initialize base with a placeholder; discover() replaces source_path.
        # Инициализируем базу заглушкой; discover() заменяет source_path.
        super().__init__(Path("."))

    def discover(self) -> List[Skill]:
        """Download repo, extract, and discover skills.

        Скачать репозиторий, распаковать и обнаружить навыки.

        Returns:
            List of discovered skills. / Список обнаруженных навыков.
        """
        owner, repo = _parse_github_url(self.repo_url)

        archive_path = _download_archive(owner, repo, self.tree)
        try:
            # Create a temp directory for extraction.
            # Создаём временную директорию для распаковки.
            self._extracted_dir = Path(tempfile.mkdtemp())
            _extract_archive(archive_path, self._extracted_dir)

            repo_root = _find_extracted_root(self._extracted_dir)
            # Normalize subpath to a list for uniform processing.
            # Приводим subpath к списку для единообразной обработки.
            subpaths = (
                self.subpath
                if isinstance(self.subpath, list)
                else [self.subpath]
            )

            all_skills: List[Skill] = []
            for sp in subpaths:
                scan_path = repo_root / sp
                if not scan_path.exists():
                    # Missing subpath is not fatal; log and continue.
                    # Отсутствующий подпуть не является фатальным; логируем и продолжаем.
                    logger.error("subpath not found: %s", scan_path)
                    continue

                # Delegate actual discovery to AutoDiscovery for each subpath.
                # Делегируем непосредственное обнаружение AutoDiscovery для каждого подпути.
                github_source = GitHubSource(
                    repo_url=self.repo_url,
                    tree=self.tree,
                    subpath=sp,
                )
                all_skills.extend(
                    AutoDiscovery(scan_path, source=github_source).discover()
                )

            return all_skills
        finally:
            # Always remove the downloaded archive.
            # Всегда удаляем скачанный архив.
            archive_path.unlink(missing_ok=True)

    def cleanup(self) -> None:
        """Remove the extracted archive directory.

        Удалить распакованную директорию архива.
        """
        if self._extracted_dir is not None and self._extracted_dir.exists():
            shutil.rmtree(self._extracted_dir)
            self._extracted_dir = None
