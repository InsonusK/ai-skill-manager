"""Abstract role for copying discovered skills into a target directory.

Абстрактная роль для копирования обнаруженных скиллов в целевую директорию.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import AbstractSet, Dict, Optional, TYPE_CHECKING

from ...progress import ProgressCallback

if TYPE_CHECKING:
    from ...entities.skill_v2 import Skill


class CopySkills(ABC):
    """Copies every skill in the dict into one target directory - step 3.

    Копирует каждый скилл из словаря в одну целевую директорию - шаг 3.

    Each configured target picks one implementation (composed via
    decoration for flavors that add behavior on top of the default copy),
    so a new target flavor means a new implementation, not edits to a
    shared adapter list.

    Каждый настроенный target выбирает одну реализацию (составленную через
    декорирование для вариантов, добавляющих поведение поверх копирования
    по умолчанию), поэтому новый вариант target'а означает новую
    реализацию, а не правки общего списка адаптеров.
    """

    @abstractmethod
    def copy(
        self,
        skills: Dict[str, "Skill"],
        target_dir: Path,
        source_repo_path: Path,
        output_repo_path: Path,
        skip_names: AbstractSet[str] = frozenset(),
        progress: Optional[ProgressCallback] = None,
    ) -> Dict[str, Path]:
        """Copy every skill and return its name mapped to its copied directory.

        Копирует каждый скилл и возвращает отображение его имени на
        скопированную директорию.

        Args:
            skills: The *full* set of skills, including any named in
                ``skip_names`` - needed so links to a skipped skill still
                resolve correctly, even though that skill's own files are
                not touched.
                / *Полный* набор скиллов, включая перечисленные в
                ``skip_names`` - нужен, чтобы ссылки на пропущенный скилл
                всё равно корректно резолвились, даже если файлы этого
                скилла не трогаются.
            skip_names: Names of skills already correctly in place at
                ``target_dir / name`` - their files must not be copied or
                rewritten again.
                / Имена скиллов, уже корректно находящихся в
                ``target_dir / name`` - их файлы не должны копироваться или
                переписываться повторно.
            progress: Optional ``(stage, current, total)`` callback for
                progress reporting. / Опциональный callback для отчёта о
                прогрессе.
        """
        ...
