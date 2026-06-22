"""Utility functions for ai-skills.

Вспомогательные функции для работы с AI-навыками.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional
from .entities import Skill

# EN: Marker file created inside directories managed by this tool.
# RU: Маркерный файл, создаваемый внутри директорий, управляемых этим инструментом.
MANAGER_TAG_FILE = ".ai-skills-managed"


def compute_skill_hash(skill: Skill) -> str:
    """Compute hash of a skill source.

    Вычисляет хеш источника навыка.
    """
    # EN: Flat skills are represented by a single file.
    # RU: Плоские навыки представлены одним файлом.
    if skill.is_flat():
        return compute_hash(skill.file_path)

    # EN: Directory skills are hashed from the relative paths and contents of all files.
    # RU: Директорийные навыки хешируются по относительным путям и содержимому всех файлов.
    h = hashlib.sha256()
    for file_path in sorted([f.path for f in skill.files]):
        if file_path.is_file():
            # EN: Include the relative path so renaming a file changes the hash.
            # RU: Включаем относительный путь, чтобы переименование файла меняло хеш.
            rel = str(file_path.relative_to(skill.folder_path))
            h.update(rel.encode())
            h.update(compute_hash(file_path).encode())
    return h.hexdigest()


def compute_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file.

    Вычисляет SHA256 хеш файла.
    """
    h = hashlib.sha256()
    # EN: Read the file in chunks to keep memory usage low for large files.
    # RU: Читаем файл частями, чтобы снизить потребление памяти для больших файлов.
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


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
