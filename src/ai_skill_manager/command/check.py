"""Check command business logic.

Discovers skills, validates them, and returns the result.
No console output is produced here.

Обнаруживает навыки, проверяет их и возвращает результат.
Здесь не производится консольный вывод.
"""

from typing import List, Optional, Tuple

from ..entities import Source
from ..progress import ProgressCallback
from ..service.discover import discover
from ..service.validate import validate
from ..validators import ValidationReport


def run_check(
    sources: List[Source],
    progress: Optional[ProgressCallback] = None,
) -> Tuple[List, ValidationReport]:
    """Discover skills from ``sources`` and validate them.

    Обнаруживает навыки из ``sources`` и проверяет их.

    Args:
        sources: Skill sources to scan. / Источники навыков для сканирования.
        progress: Optional ``(stage, current, total)`` callback for progress
            reporting. / Опциональный callback для отчёта о прогрессе.

    Returns:
        Tuple of ``(skills, report)``. / Кортеж ``(навыки, отчёт)``.
    """
    skills = discover(sources, progress=progress)
    report = validate(skills, progress=progress)
    return skills, report
