"""Hash a discovered (new-model) skill's own content.

Хеширование собственного содержимого обнаруженного скилла (новая модель).
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from ..functions.hash import compute_hash
from ..entities.skill_kind import SkillKind

if TYPE_CHECKING:
    from ..entities.skill_v2 import Skill


def compute_skill_hash(skill: "Skill") -> str:
    """Compute a content hash of ``skill``'s own files.

    Вычисляет хеш содержимого собственных файлов ``skill``.

    Requires ``skill.files`` to already be populated (via
    ``file_discovery.discover``). Includes each file's relative path so
    renaming a file changes the hash.

    Требует, чтобы ``skill.files`` уже был заполнен (через
    ``file_discovery.discover``). Включает относительный путь каждого файла,
    чтобы переименование файла меняло хеш.
    """
    if skill.kind is SkillKind.flat:
        return compute_hash(skill.path)

    digest = hashlib.sha256()
    for skill_file in sorted(skill.files, key=lambda f: f.path.as_posix()):
        file_path = skill.path / skill_file.path
        if not file_path.is_file():
            continue
        digest.update(str(skill_file.path).encode())
        digest.update(compute_hash(file_path).encode())
    return digest.hexdigest()
