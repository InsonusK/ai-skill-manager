from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass
class SkillMapping:
    """Maps a source to a target skill."""
    source_path: Path
    target_path: Path
    skill_name: str
    is_flat: bool
    source_skill_md: Optional[Path] = field(default=None)