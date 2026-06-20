from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ....models import Skill


@dataclass(frozen=True)
class FileContext:
    """Context for a single file inside a skill.

    Attributes:
        path: Path to the file on disk.
        skill: The skill the file belongs to, if known.
        content: Optional file content. When omitted, content is read from disk.
    """

    path: Path
    skill: Skill
