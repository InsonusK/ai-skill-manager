"""Exception raised when sync fails to materialize one or more skills.

Исключение, возникающее, когда синхронизации не удалось материализовать
один или несколько скиллов.
"""

from pathlib import Path
from typing import List

from .adapters.models.sync_error import SyncError


class SyncFailedError(Exception):
    """Raised when materialization collected one or more errors.

    The target directory is left untouched: nothing is moved into it while
    any error is outstanding. The staging directory is kept (not cleaned up)
    so the failures can be inspected on disk.

    Возникает, когда материализация собрала одну или несколько ошибок.
    Целевая директория остаётся нетронутой: пока есть хотя бы одна
    незакрытая ошибка, в неё ничего не переносится. Директория staging
    сохраняется (не очищается), чтобы ошибки можно было изучить на диске.
    """

    __slots__ = ("errors", "staging_dir", "target_dir")

    def __init__(self, errors: List[SyncError], staging_dir: Path, target_dir: Path):
        """Initialize the exception with the collected errors and paths.

        Args:
            errors: Failures collected during materialization.
                / Ошибки, собранные во время материализации.
            staging_dir: Staging directory kept for inspection.
                / Директория staging, сохранённая для изучения.
            target_dir: Target directory that was left untouched.
                / Целевая директория, оставшаяся нетронутой.
        """
        self.errors = errors
        self.staging_dir = staging_dir
        self.target_dir = target_dir
        super().__init__(
            f"Sync failed with {len(errors)} error(s); {target_dir} was left "
            f"unchanged. Inspect the staged output at {staging_dir}."
        )
