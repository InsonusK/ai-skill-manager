from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Skill:
    file_path: Path
    folder_path: Path|None
    def is_flat(self)->bool:
        return self.folder_path is None