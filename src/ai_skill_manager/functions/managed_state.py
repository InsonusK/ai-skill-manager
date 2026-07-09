"""Managed-state helpers for directories controlled by ai-skill-manager.

Вспомогательные функции для управляемого состояния директорий,
контролируемых ai-skill-manager.
"""

import json
from pathlib import Path
from typing import Optional

# EN: Marker file created inside directories managed by this tool.
# RU: Маркерный файл, создаваемый внутри директорий, управляемых этим инструментом.
MANAGER_TAG_FILE = ".ai-skills-managed"


def is_managed(skill_dir: Path) -> bool:
    """Check if directory was created by this tool.

    Проверяет, была ли директория создана этим инструментом.
    """
    return (skill_dir / MANAGER_TAG_FILE).exists()


def tag_managed(skill_dir: Path) -> None:
    """Mark directory as managed by this tool.

    Помечает директорию как управляемую этим инструментом.
    """
    (skill_dir / MANAGER_TAG_FILE).touch()


def read_managed_state(skill_dir: Path) -> Optional[dict]:
    """Read managed state from skill directory.

    Читает управляемое состояние из директории навыка.
    """
    path = skill_dir / MANAGER_TAG_FILE
    if not path.exists():
        return None
    try:
        # EN: Parse the JSON state stored in the marker file.
        # RU: Парсим JSON-состояние, сохранённое в маркерном файле.
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        # EN: Treat malformed state as absent.
        # RU: Считаем повреждённое состояние отсутствующим.
        return None


def write_managed_state(skill_dir: Path, state: dict) -> None:
    """Write managed state to skill directory.

    Записывает управляемое состояние в директорию навыка.
    """
    path = skill_dir / MANAGER_TAG_FILE
    path.write_text(json.dumps(state, indent=2), encoding='utf-8')
