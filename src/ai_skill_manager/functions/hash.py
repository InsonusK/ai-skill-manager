"""Hashing helpers for files.

Вспомогательные функции хеширования файлов.
"""

import hashlib
from pathlib import Path


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
