from dataclasses import dataclass
from pathlib import Path

from ....models import Skill


@dataclass(frozen=True)
class FileContext:
    """Context for a single file inside a skill.

    Attributes:
        path: Path to the file on disk.
        skill: The skill the file belongs to.
    """

    path: Path
    skill: Skill
