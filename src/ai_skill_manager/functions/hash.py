"""Hashing helpers for skills and files.

Вспомогательные функции хеширования навыков и файлов.
"""

import hashlib
from pathlib import Path

from ..entities import Skill


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
