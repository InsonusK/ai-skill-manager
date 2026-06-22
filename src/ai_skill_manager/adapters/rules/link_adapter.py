from typing import List, Optional, Tuple

from ...entities import Link, Skill, SkillFile
from ...models import LinkWithContext
from .abs_adapter import absAdapter


class LinkAdapter(absAdapter):
    def __init__(self, adapter_context):
        super().__init__(adapter_context)
        self.links_replaced = 0

    @classmethod
    def version(cls) -> str:
        """Adapter version for change detection."""
        return "1.0.0"

    def adapt(self, old_skill: Skill, new_skill: Skill) -> None:
        """Rewrite links in ``skill`` files to the skill-link format.

        Переписывает ссылки в файлах ``skill`` в формат skill-link.
        """
        other_skills = [s for s in self._adapter_context.skills if s is not old_skill]
        for skill_file in new_skill.files:
            content = skill_file.path.read_text(encoding="utf-8")
            new_content, count = self._replace_links(
                content, skill_file.links, skill_file, new_skill, other_skills
            )
            if count:
                skill_file.path.write_text(new_content, encoding="utf-8")
            self.links_replaced += count

    def _replace_links(
        self,
        content: str,
        links: Tuple[Link, ...],
        skill_file: SkillFile,
        skill: Skill,
        other_skills: List[Skill],
    ) -> Tuple[str, int]:
        """Replace all links in ``content`` with skill-link format.

        Заменяет все ссылки в ``content`` на формат skill-link.

        Replacements are applied from the end of the content to the start so that
        offsets remain valid.

        Замены применяются с конца содержимого к началу, чтобы смещения
        оставались корректными.
        """
        replaced = 0
        sorted_links = sorted(links, key=lambda link: link.start, reverse=True)

        for link in sorted_links:
            new_target = self._compute_new_target(link, skill_file, skill, other_skills)

            prefix = "!" if link.is_image else ""
            new_raw = f"{prefix}[{link.text}]({new_target})"
            content = content[: link.start] + new_raw + content[link.end :]
            replaced += 1

        return content, replaced

    def _compute_new_target(
        self,
        link: Link,
        skill_file: SkillFile,
        skill: Skill,
        other_skills: List[Skill],
    ) -> Optional[str]:
        """Compute the skill-link replacement target for a link.

        Вычисляет цель замены ссылки в формате skill-link.

        Returns:
            The new link target, or ``None`` if the link should be left unchanged
            (for example external URLs).
            Новая цель ссылки или ``None``, если ссылку следует оставить без
            изменений (например, внешние URL).
        """
        link_context = LinkWithContext.build(skill, skill_file, link)
        new_target = link_context.to_skill_format(other_skills)
        if link.header:
            new_target += link.header
        return new_target
