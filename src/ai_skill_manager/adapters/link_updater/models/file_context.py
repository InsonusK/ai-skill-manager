from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from ....models import Skill


@dataclass(frozen=True)
class FileContext:
    path: Path
    skill: Skill
