"""Adapter that rewrites links into the skill-link format.

Адаптер, переписывающий ссылки в формат skill-link.
"""

from typing import List, Optional, Tuple

from ...entities import Link, LinkKind, Skill, SkillFile
from ...models import LinkWithContext
from ..models.adapter_message import AdapterMessage
from .abs_adapter import absAdapter


class LinkAdapter(absAdapter):
    """Rewrites internal links in copied skill files to skill-link targets."""

    def __init__(self, adapter_context):
        """Initialize the adapter and reset the replacement counter.

        Args:
            adapter_context: Shared adapter context.
                / Общий контекст адаптера.
        """
        super().__init__(adapter_context)
        # Count of links replaced during the last adaptation.
        # Счётчик заменённых ссылок во время последней адаптации.
        self.links_replaced = 0

    @classmethod
    def version(cls) -> str:
        """Adapter version for change detection.

        Версия адаптера для обнаружения изменений.
        """
        return "1.0.0"

    def adapt(self, old_skill: Skill, new_skill: Skill) -> AdapterMessage:
        """Rewrite links in ``new_skill`` files to the skill-link format.

        Переписывает ссылки в файлах ``new_skill`` в формат skill-link.

        Args:
            old_skill: Original skill before copying.
                / Исходный навык до копирования.
            new_skill: Copied skill in the target directory.
                / Скопированный навык в целевой директории.

        Returns:
            Message summarizing how many links were replaced.
                / Сообщение с количеством заменённых ссылок.
        """
        self.links_replaced = 0

        # Exclude the old skill itself when resolving links to other skills.
        # Исключаем сам старый навык при разрешении ссылок на другие навыки.
        other_skills = [s for s in self._adapter_context.skills if s is not old_skill]

        for skill_file in new_skill.files:
            # Read the full file content once.
            # Читаем полное содержимое файла один раз.
            content = skill_file.path.read_text(encoding="utf-8")

            new_content, count = self._replace_links(
                content, skill_file.links, skill_file, new_skill, other_skills
            )

            # Write only if at least one link was replaced.
            # Записываем только если хотя бы одна ссылка была заменена.
            if count:
                skill_file.path.write_text(new_content, encoding="utf-8")

            self.links_replaced += count

        return AdapterMessage(
            message="Replaced {count} links",
            params={"count": self.links_replaced},
        )

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

        Args:
            content: Original file content.
                / Исходное содержимое файла.
            links: Links found in the file.
                / Ссылки, найденные в файле.
            skill_file: File that contains the links.
                / Файл, содержащий ссылки.
            skill: Skill that owns the file.
                / Навык, которому принадлежит файл.
            other_skills: Other known skills for resolving skill links.
                / Другие известные навыки для разрешения ссылок на навыки.

        Returns:
            Updated content and the number of replacements made.
                / Обновлённое содержимое и количество выполненных замен.
        """
        replaced = 0

        # Sort links by start position descending to keep string offsets valid.
        # Сортируем ссылки по начальной позиции по убыванию, чтобы смещения строк оставались корректными.
        sorted_links = sorted(links, key=lambda link: link.start, reverse=True)

        for link in sorted_links:
            new_target = self._compute_new_target(link, skill_file, skill, other_skills)
            if new_target is None:
                # Nothing to do for this link.
                # Для этой ссылки ничего делать не нужно.
                continue

            # Preserve image prefix (!) when rebuilding the markdown link.
            # Сохраняем префикс изображения (!) при перестроении markdown-ссылки.
            prefix = "!" if link.is_image else ""
            new_raw = f"{prefix}[{link.text}]({new_target})"

            # Replace the original link slice with the new markdown text.
            # Заменяем исходный фрагмент ссылки на новый markdown-текст.
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

        Args:
            link: Link to rewrite.
                / Ссылка для перезаписи.
            skill_file: File containing the link.
                / Файл, содержащий ссылку.
            skill: Skill that owns the file.
                / Навык, которому принадлежит файл.
            other_skills: Other known skills.
                / Другие известные навыки.

        Returns:
            The new link target, or ``None`` if the link should be left unchanged
            (for example external URLs).
            Новая цель ссылки или ``None``, если ссылку следует оставить без
            изменений (например, внешние URL).
        """
        # External links are never rewritten.
        # Внешние ссылки никогда не переписываются.
        if link.kind == LinkKind.web:
            return None

        # Build context and resolve the skill-format target.
        # Формируем контекст и разрешаем цель в формате skill-link.
        link_context = LinkWithContext.build(skill, skill_file, link)
        new_target = link_context.to_skill_format(other_skills)

        # Preserve the original link header/anchor if present.
        # Сохраняем оригинальный якорь/заголовок ссылки, если он есть.
        if link.header:
            new_target += link.header

        return new_target
