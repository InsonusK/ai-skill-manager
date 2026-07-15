"""Copy a file that doesn't belong to any skill into a shared files/ directory.

Копирование файла, не принадлежащего ни одному скиллу, в общую директорию
files/.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict


class ExternalFileCopier:
    """Copies external files into ``{target_dir}/files/``, deduped per target.

    Копирует внешние файлы в ``{target_dir}/files/``, с дедупликацией в
    рамках одного target'а.

    Shared across every skill copied into the same target run: a file
    referenced by several skills is copied once, not once per skill.

    Общий для всех скиллов, копируемых в один и тот же прогон target'а:
    файл, на который ссылаются несколько скиллов, копируется один раз, а
    не по разу на каждый скилл.
    """

    def __init__(self) -> None:
        """Initialize the copy registry (repo-absolute path -> path relative to target)."""
        self._copied: Dict[Path, Path] = {}

    def copy(self, repo_absolute_path: Path, repo_path: Path, target_dir: Path) -> Path:
        """Copy the file/directory at ``repo_absolute_path`` and return its new relative path.

        Копирует файл/директорию по ``repo_absolute_path`` и возвращает её
        новый относительный путь.

        Returns:
            Path relative to ``target_dir``, e.g. ``files/diagram.png``.
                / Путь относительно ``target_dir``, например ``files/diagram.png``.
        """
        if repo_absolute_path in self._copied:
            return self._copied[repo_absolute_path]

        source = repo_path / repo_absolute_path
        files_dir = target_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        destination = files_dir / source.name
        counter = 1
        stem, suffix = source.stem, source.suffix
        while destination.exists():
            destination = files_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

        relative = destination.relative_to(target_dir)
        self._copied[repo_absolute_path] = relative
        return relative
