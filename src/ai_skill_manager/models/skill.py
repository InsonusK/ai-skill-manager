from dataclasses import dataclass, field
from pathlib import Path
from .skill_propetry import SkillProperty

from .skill_format import SkillFormat
from .source import Source


@dataclass(frozen=True)
class Skill:
    """Represents a discovered skill on disk.

    Представляет обнаруженный навык на диске.
    """

    file_path: Path
    folder_path: Path | None
    source: Source
    format: SkillFormat  # Required skill format. / Обязательный формат навыка.
    properties: SkillProperty = field(init=False)
    
    def __post_init__(self):
        # Обход frozen через object.__setattr__
        object.__setattr__(self, "properties", SkillProperty(self.file_path))
    
    @property
    def is_flat(self) -> bool:
        return self.folder_path is None
    
    @property
    def is_dir(self)->bool:
        return not self.is_flat
    
    
    