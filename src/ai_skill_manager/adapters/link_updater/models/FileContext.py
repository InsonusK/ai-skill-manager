from dataclasses import dataclass
from pathlib import Path
from ....models import Skill


@dataclass
class FileContext:
    path: Path
    skill: Skill

    def __post_init__(self):
        if self.skill.is_flat():
            if self.path != self.skill.file_path:
                raise ValueError(
                    f"Flat skill path must equal skill file path: "
                    f"{self.path} != {self.skill.file_path}"
                )
        else:
            folder_path = self.skill.folder_path
            if folder_path is None:
                raise ValueError(
                    "Non-flat skill must have a folder path"
                )
            if not self.path.is_relative_to(folder_path):
                raise ValueError(
                    f"Path must be inside skill folder: {self.path} "
                    f"is not relative to {folder_path}"
                )
