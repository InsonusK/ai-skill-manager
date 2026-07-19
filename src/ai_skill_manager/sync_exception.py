"""Exception raised when sync fails to discover, enrich, or copy skills.

Исключение, возникающее, когда синхронизации не удалось обнаружить,
обогатить или скопировать скиллы.
"""

from pathlib import Path
from typing import List, Union

from .models.link_validation_error import LinkValidationError


class SyncFailedError(Exception):
    """Raised when discovery/enrichment collected one or more errors.

    Nothing is ever copied while any error is outstanding: resolution
    happens entirely in memory before any file is written, so a failure
    leaves the target directory exactly as it was before the run - there is
    no partial or staged output to inspect.

    Возникает, когда обнаружение/обогащение собрало одну или несколько
    ошибок. Пока есть хотя бы одна незакрытая ошибка, ничего не копируется:
    резолюция происходит полностью в памяти до записи любого файла, поэтому
    сбой оставляет целевую директорию точно в том состоянии, в котором она
    была до запуска - никакого частичного или промежуточного вывода для
    изучения нет.
    """

    __slots__ = ("errors", "target_dir")

    def __init__(self, errors: List[Union[str, LinkValidationError]], target_dir: Path):
        """Initialize the exception with the collected errors and target path.

        Args:
            errors: Failures collected during discovery/enrichment.
                / Ошибки, собранные во время обнаружения/обогащения.
            target_dir: Target directory that was left untouched.
                / Целевая директория, оставшаяся нетронутой.
        """
        self.errors = errors
        self.target_dir = target_dir
        super().__init__(
            f"Sync failed with {len(errors)} error(s); {target_dir} was left unchanged."
        )
