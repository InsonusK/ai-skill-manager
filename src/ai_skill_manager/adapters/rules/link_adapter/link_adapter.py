"""Adapter that rewrites links into the skill-link format.

Адаптер, переписывающий ссылки в формат skill-link.
"""

from typing import List, Optional, Tuple

from ....entities import Skill, SkillFile, WebLink, absLink
from ....validators.rules.link_validation_rule import _is_inside_inline_code
from ...models.adapter_message import AdapterMessage
from ..abs_adapter import absAdapter
from .converter import LinkConverter


class LinkAdapter(absAdapter):
    """Rewrites internal links in copied skill files to skill-link targets."""

    def __init__(self, adapter_context: absAdapter.Context):
        """Initialize the adapter and reset the replacement counter.

        Args:
            adapter_context: Shared adapter context.
                / Общий контекст адаптера.
        """
        super().__init__(adapter_context)
        # Count of links replaced during the last adaptation.
        # Счётчик заменённых ссылок во время последней адаптации.
        self.links_replaced = 0
        self._link_converter = LinkConverter()

    @classmethod
    def version(cls) -> str:
        """Adapter version for change detection.

        Версия адаптера для обнаружения изменений.
        """
        return "1.2.0"

    def adapt(self, old_skill: Skill, new_skill: Skill) -> AdapterMessage:
        """Rewrite links in ``new_skill`` files to the repo-absolute format.

        Переписывает ссылки в файлах ``new_skill`` в формат repo-absolute.

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
            links = skill_file.links
            if not links:
                # Nothing to rewrite in this file.
                # В этом файле нечего переписывать.
                continue

            # Skip files where every link is an external URL; they are never
            # rewritten, so reading the file would be wasted work.
            # Пропускаем файлы, где все ссылки — внешние URL; они никогда не
            # переписываются, поэтому чтение файла было бы лишней работой.
            if all(isinstance(link, WebLink) for link in links):
                continue

            # Read the full file content once.
            # Читаем полное содержимое файла один раз.
            content = skill_file.path.read_text(encoding="utf-8")

            new_content, count = self._replace_links(
                content, links, skill_file, new_skill, other_skills
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
        links: Tuple[absLink, ...],
        skill_file: SkillFile,
        skill: Skill,
        other_skills: List[Skill],
    ) -> Tuple[str, int]:
        """Replace all links in ``content`` with repo-absolute format.

        Заменяет все ссылки в ``content`` на формат repo-absolute.

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
        # The original order is preserved so that external file name collision
        # resolution stays deterministic.
        # Сортируем ссылки по начальной позиции по убыванию, чтобы смещения
        # строк оставались корректными. Исходный порядок сохраняем, чтобы
        # разрешение коллизий имён внешних файлов оставалось детерминированным.
        sorted_links = sorted(links, key=lambda link: link.start, reverse=True)

        # Collect content fragments and replacements while walking from the end
        # of the string toward the beginning, then join once. This avoids the
        # O(n²) cost of repeated string slicing.
        # Собираем фрагменты содержимого и замены, двигаясь от конца строки к
        # началу, затем один раз объединяем. Это позволяет избежать
        # квадратичной сложности повторной нарезки строк.
        fragments: List[str] = []
        last_start = len(content)

        for link in sorted_links:
            # Skip links inside inline code spans (`...`), just like validation.
            # Examples like `[text](path)` in anti-patterns should not be treated
            # as real links and must not trigger file copies.
            if _is_inside_inline_code(content, link.start, link.end):
                continue

            new_target = self._compute_new_target(link, skill_file, skill, other_skills)
            if new_target is None:
                # Nothing to do for this link.
                # Для этой ссылки ничего делать не нужно.
                continue

            # Preserve image prefix (!) when rebuilding the markdown link.
            # Сохраняем префикс изображения (!) при перестроении markdown-ссылки.
            prefix = "!" if link.is_image else ""
            new_raw = f"{prefix}[{link.text}]({new_target})"

            # Append the unchanged text after this link and the replacement.
            # The collected fragments are reversed at the end to restore the
            # natural left-to-right order.
            # Добавляем неизменённый текст после ссылки и саму замену. Собранные
            # фрагменты в конце переворачиваются, чтобы восстановить естественный
            # порядок слева направо.
            fragments.append(content[link.end : last_start])
            fragments.append(new_raw)
            last_start = link.start
            replaced += 1

        # Append the leading part of the content before the first replacement.
        # Добавляем начальную часть содержимого перед первой заменой.
        fragments.append(content[:last_start])

        # Reverse the fragments so they read from the start of the file to the
        # end, then build the final string in one shot.
        # Переворачиваем фрагменты, чтобы они шли от начала файла к концу, и
        # собираем итоговую строку за один приём.
        fragments.reverse()
        return "".join(fragments), replaced

    def _compute_new_target(
        self,
        link: absLink,
        skill_file: SkillFile,
        skill: Skill,
        other_skills: List[Skill],
    ) -> Optional[str]:
        """Compute the repo-absolute replacement target for a link.

        Вычисляет цель замены ссылки в формате repo-absolute.

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
        if isinstance(link, WebLink):
            return None

        # Resolve the repo-absolute target via the dedicated converter.
        # Pass the source-to-target skill mapping so source links that still
        # point to the original source paths can be resolved correctly.
        # Pass the target skill folder and the shared copy registry so that
        # links to files outside any skill can be copied into files/.
        # Разрешаем цель в формате repo-absolute через специализированный конвертер.
        # Передаём маппинг исходных скиллов в целевые, чтобы source-ссылки,
        # всё ещё указывающие на исходные пути, разрешались корректно.
        # Передаём целевую папку скилла и общий реестр копирования, чтобы
        # ссылки на файлы вне скиллов можно было скопировать в files/.
        return self._link_converter.convert(
            link,
            other_skills,
            self._adapter_context.skill_mapping,
            target_skill_folder=skill.folder_path,
            copied_files=self._adapter_context.copied_files,
        )
