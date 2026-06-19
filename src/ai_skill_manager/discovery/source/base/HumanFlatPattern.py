from .SkillPattern import SkillPattern,Skill,SkillFormat,Optional
from pathlib import Path


class HumanFlatPattern(SkillPattern):
    """Flat human skill: a single ``*.skill.md`` file."""

    skill_format = SkillFormat.HumanFlat

    def match(self, path: Path) -> Optional[Skill]:
        if path.is_file() and path.name.endswith(".skill.md"):
            return Skill(
                file_path=path,
                folder_path=None,
                format=self.skill_format,
            )
        return None