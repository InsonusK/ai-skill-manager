from dataclasses import dataclass
from pathlib import Path
from ..entities import SkillFile,Skill

@dataclass(frozen=True)
class LinkLocation:
    """Where a link was found in the source text.

    Attributes:
        file: The file context for the file containing the link.
        start: Character offset where the link starts in the content.
        end: Character offset where the link ends in the content.
    """

    file: SkillFile
    skill: Skill
    
    @property
    def filepath(self) -> Path:
        """Backward-compatible alias for :attr:`file.path`."""
        return self.file.path
    
    def __post_init__(self):
        skill_files = [file for file in self.skill.files if file == self.file]
        assert len(skill_files)>0, f"File {self.file.path} doesn't find in files of skill {self.skill.file_path}"
        assert len(skill_files)==1, f"File {self.file.path} has more than 1 candidate in files of skill {self.skill.file_path}"