from .SkillPattern import SkillPattern, Skill, SkillFormat, Optional


from pathlib import Path


class HumanDirPattern(SkillPattern):
    """Directory human skill: ``{dir_name}.skill.md`` inside a directory."""

    skill_format = SkillFormat.HumanDir

    def match(self, path: Path) -> Optional[Skill]:
        if not path.is_dir():
            return None
        skill_md = path / f"{path.name}.skill.md"
        if skill_md.is_file():
            return Skill(
                file_path=skill_md,
                folder_path=path,
                format=self.skill_format,
            )
        return None
