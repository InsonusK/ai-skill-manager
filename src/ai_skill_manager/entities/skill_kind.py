"""Skill kind (shape on disk).

Тип скилла (форма на диске).
"""

from enum import Enum


class SkillKind(Enum):
    """Whether a skill is a single file or a directory.

    Является ли скилл одним файлом или директорией.
    """

    flat = "flat"
    """A single markdown file. / Единственный markdown-файл."""

    dir = "dir"
    """A directory containing a main file and, optionally, other files.

    Директория, содержащая основной файл и, опционально, другие файлы.
    """
