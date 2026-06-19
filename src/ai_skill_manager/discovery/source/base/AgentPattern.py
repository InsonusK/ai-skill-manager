from .SkillPattern import SkillPattern, Skill, SkillFormat,Optional
from pathlib import Path


class AgentPattern(SkillPattern):
    """Agent skill: ``SKILL.md`` inside a directory."""

    skill_format = SkillFormat.Agent

    def match(self, path: Path) -> Optional[Skill]:
        if not path.is_dir():
            return None
        skill_md = path / "SKILL.md"
        if skill_md.is_file():
            return Skill(
                file_path=skill_md,
                folder_path=path,
                format=self.skill_format,
            )
        return None