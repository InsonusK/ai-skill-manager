"""Git CLI based repository cloning.

Клонирование репозиториев через git CLI.
"""

import logging
import shutil
import subprocess
from pathlib import Path

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


class GitCloneError(RuntimeError):
    """Raised when a repository cannot be cloned via the git CLI.

    Возбуждается, когда репозиторий не может быть склонирован через git CLI.
    """


def clone_git_repo(repo_url: str, tree: str, dest_dir: Path) -> Path:
    """Clone a git repository at a given ref into a destination directory.

    Склонировать git-репозиторий на заданном ref в целевую директорию.

    Unlike the anonymous HTTPS archive download, cloning goes through the
    git CLI, so the user's own credentials apply: SSH keys, SSH agent,
    https credential helpers and per-host URL rewrites. That is what makes
    private repositories reachable.

    В отличие от анонимного скачивания архива по HTTPS, клонирование идёт
    через git CLI, поэтому используются собственные учётные данные
    пользователя: SSH-ключи, SSH-агент, credential helpers и перезапись
    URL для конкретных хостов. Именно это делает доступными приватные
    репозитории.

    Args:
        repo_url: Any URL or path accepted by ``git clone`` (https, ssh,
            git@host:..., file://, local path).
            / Любой URL или путь, принимаемый ``git clone``.
        tree: Branch or tag to check out. / Ветка или тег для checkout.
        dest_dir: Existing-or-created empty directory to clone into.
            / Директория для клонирования.

    Returns:
        Path to the cloned repository root. / Путь к корню склонированного репозитория.

    Raises:
        GitCloneError: If git is not installed or the clone command fails.
            / Если git не установлен или команда clone завершилась с ошибкой.
    """
    if shutil.which("git") is None:
        raise GitCloneError("git executable not found in PATH; cannot clone repository")

    cmd = [
        "git",
        "clone",
        "--quiet",
        "--depth",
        "1",
        "--branch",
        tree,
        repo_url,
        str(dest_dir),
    ]
    logger.debug("Cloning git repository: %s (tree=%s)", repo_url, tree)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        logger.debug("git clone failed for %s: %s", repo_url, stderr)
        raise GitCloneError(f"git clone failed for {repo_url} (tree={tree}): {stderr}")
    logger.debug("Cloned %s into %s", repo_url, dest_dir)
    return dest_dir
