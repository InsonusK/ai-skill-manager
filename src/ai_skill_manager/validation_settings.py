"""Validation-related settings shared between validators and adapters.

Настройки валидации, общие для валидаторов и адаптеров.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ValidationSettings:
    """Validation-related settings from the config file.

    Настройки валидации из файла конфигурации.
    """

    link_skip_folders: Optional[List[str]] = None
    """Folder names whose files are skipped during link validation/adaptation.

    ``None`` means use the built-in default (``["examples"]``). An empty list
    disables folder-based exclusions entirely.

    Имена директорий, файлы которых пропускаются при валидации/адаптации
    ссылок. ``None`` означает использование встроенного умолчания
    (``["examples"]``). Пустой список полностью отключает исключения по
    директориям.
    """
