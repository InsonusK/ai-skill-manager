"""Exclude rule for files inside configured folders.

Правило исключения файлов, находящихся в настроенных директориях.
"""

from typing import List

from ....models import LinkWithContext
from .abs_exclude_rule import absExcludeRule


class SkipFolderExcludeRule(absExcludeRule):
    """Skip links found in files located under any of the configured folders.

    By default the ``examples`` directory is excluded. Pass an empty list to
    disable exclusions, or a custom list to override the default.

    По умолчанию исключается директория ``examples``. Пустой список отключает
    исключения, а произвольный список заменяет умолчание.
    """

    DEFAULT_SKIP_FOLDERS = ("examples",)

    def __init__(self, skip_folders: List[str] | None = None):
        """Initialize with an optional folder list.

        Args:
            skip_folders: Folder names that exclude a file from validation.
                ``None`` means use the default (``examples``).
                / Имена директорий, исключающих файл из валидации.
                ``None`` означает использование умолчания (``examples``).
        """
        if skip_folders is None:
            skip_folders = list(self.DEFAULT_SKIP_FOLDERS)
        self._skip_folders = set(skip_folders)

    def should_exclude(self, link: LinkWithContext) -> bool:
        """Return ``True`` if the link's file is inside one of the skip folders."""
        return any(part in self._skip_folders for part in link.file_path.parts)
