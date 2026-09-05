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

from .git_clone import GitCloneError, clone_git_repo
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


    
def fetch_repo_tree(repo_url: str, tree: str, work_dir: Path) -> Path:
    """Materialize a repository at a given ref, preferring git clone.

    Материализовать содержимое репозитория на заданном ref, предпочитая git clone.

    Git clone goes through the git CLI, so the user's own credentials apply
    (SSH keys, credential helpers, URL rewrites) and any git host works —
    that is what makes private repositories reachable. The anonymous GitHub
    archive download remains only as a fallback for when git is unavailable
    or the clone fails and the URL is a GitHub one.

    Клонирование идёт через git CLI, поэтому используются собственные
    учётные данные пользователя (SSH-ключи, credential helpers, перезапись
    URL) и работает любой git-хост — именно это делает доступными приватные
    репозитории. Анонимное скачивание архива GitHub остаётся только как
    запасной вариант, когда git недоступен или клонирование не удалось и URL
    указывает на GitHub.

    Args:
        repo_url: Any URL or path accepted by ``git clone``.
            / Любой URL или путь, принимаемый ``git clone``.
        tree: Branch or tag to check out. / Ветка или тег для checkout.
        work_dir: Existing empty directory the repository is materialized
            into (a ``repo`` or ``archive`` subdirectory is created inside).
            / Существующая пустая директория, в которую материализуется
            репозиторий (внутри создаётся поддиректория ``repo`` или
            ``archive``).

    Returns:
        Path to the repository root. / Путь к корню репозитория.

    Raises:
        GitCloneError: If cloning fails and the URL is not a GitHub URL, so
            no archive fallback is possible.
            / Если клонирование не удалось и URL не является URL GitHub, так
            что запасной вариант с архивом невозможен.
        Exception: The archive download error if both strategies fail.
            / Ошибка скачивания архива, если оба способа не удались.
    """
    clone_dir = work_dir / "repo"
    clone_error: Optional[GitCloneError] = None
    try:
        return clone_git_repo(repo_url, tree, clone_dir)
    except GitCloneError as error:
        # Bound to a separate variable: the except-block variable itself is
        # deleted when the block ends.
        # Привязана в отдельную переменную: переменная блока except удаляется
        # при выходе из блока.
        clone_error = error
        logger.warning(
            "git clone failed for %s (tree=%s), falling back to archive download: %s",
            repo_url,
            tree,
            clone_error,
        )

    if clone_dir.exists():
        # A failed clone can leave a partial directory behind; remove it so
        # the archive extraction sees exactly one top-level directory.
        # Неудачное клонирование может оставить частичную директорию;
        # удаляем её, чтобы распаковка архива видела ровно одну директорию
        # верхнего уровня.
        shutil.rmtree(clone_dir, ignore_errors=True)

    try:
        owner, repo = _parse_github_url(repo_url)
    except ValueError:
        # Not a GitHub URL — the archive fallback only works for GitHub, so
        # there is nothing else to try.
        # URL не GitHub — запасной вариант с архивом работает только для
        # GitHub, больше пробовать нечего.
        raise clone_error

    archive_dir = work_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = _download_archive(owner, repo, tree)
    try:
        _extract_archive(archive_path, archive_dir)
        return _find_extracted_root(archive_dir)
    finally:
        archive_path.unlink(missing_ok=True)


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
    @dataclass
    class Context:
        scan_cache: Optional[List[ScanLocation]] = None
        extracted_dirs: List[Path] = field(default_factory=list)

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
        extracted_dir = Path(tempfile.mkdtemp())
        self.__context.extracted_dirs.append(extracted_dir)

        repo_root = fetch_repo_tree(self.repo_url, self.tree, extracted_dir)
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
