"""Adapter that rewrites links into the skill-link format.

Адаптер, переписывающий ссылки в формат skill-link.
"""

from typing import List, Optional, Tuple

from ....entities import Skill, SkillFile, absLink
from ....entities.link.path_utils import same_path
from ....models import LinkWithContext
from ....validators.rules.link.exclude_rule import build_link_exclude_rules
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
        self._exclude_rules = build_link_exclude_rules(
            self._adapter_context.validation_settings
        )

    @classmethod
    def version(cls) -> str:
        """Adapter version for change detection.

        Версия адаптера для обнаружения изменений.
        """
        return "1.4.0"

    def adapt(self, old_skill: Skill, new_skill: Skill) -> AdapterMessage:
        """Rewrite links in ``new_skill`` files to the repo-absolute format.

        Переписывает ссылки в файлах ``new_skill`` в формат repo-absolute.

        Links are read from ``old_skill``'s own (already source-resolved)
        files rather than re-parsed from the copy. ``old_skill``'s files are
        always parsed against the true original source tree, so resolving a
        link's target is a matter of plain path containment against the other
        *source* skills - the same check link validation already performed -
        instead of re-guessing identity from a copied, differently-rooted
        path. The resolved content is then written into the corresponding
        file of ``new_skill``.

        Ссылки читаются из собственных (уже разрешённых относительно
        источника) файлов ``old_skill``, а не парсятся заново из копии. Файлы
        ``old_skill`` всегда разбираются относительно истинного исходного
        дерева, поэтому разрешение цели ссылки сводится к простой проверке
        вхождения пути среди других *исходных* скиллов — той же проверке,
        что уже выполнила валидация ссылок — вместо повторного угадывания
        идентичности по скопированному, ссылающемуся на другой корень пути.
        Полученное содержимое затем записывается в соответствующий файл
        ``new_skill``.

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

        for old_file, new_file in self._pair_files(old_skill, new_skill):
            links = old_file.links
            if not links:
                # Nothing to rewrite in this file.
                # В этом файле нечего переписывать.
                continue

            # Skip files where every link is excluded by an exclude rule; they
            # are never rewritten, so reading the file would be wasted work.
            # Пропускаем файлы, где все ссылки исключены правилами исключения;
            # они никогда не переписываются, поэтому чтение файла было бы лишней работой.
            if all(
                self._should_exclude(link, old_skill, old_file, other_skills)
                for link in links
            ):
                continue

            # Read the full (already-copied) file content once.
            # Читаем полное содержимое уже скопированного файла один раз.
            content = new_file.path.read_text(encoding="utf-8")

            new_content, count = self._replace_links(
                content, links, old_file, old_skill, other_skills
            )

            # Write only if at least one link was replaced.
            # Записываем только если хотя бы одна ссылка была заменена.
            if count:
                new_file.path.write_text(new_content, encoding="utf-8")

            self.links_replaced += count

        return AdapterMessage(
            message="Replaced {count} links",
            params={"count": self.links_replaced},
        )

    @staticmethod
    def _pair_files(old_skill: Skill, new_skill: Skill) -> List[Tuple[SkillFile, SkillFile]]:
        """Pair each source file with its copied counterpart by relative identity.

        Сопоставляет каждый исходный файл с его скопированным аналогом по
        относительной идентичности.

        The main file of a skill is renamed to ``SKILL.md`` on copy, while
        every other file keeps its relative path. Pairing by an explicit key
        (rather than by list position) stays correct regardless of that
        rename or of directory-listing order.

        Основной файл скилла при копировании переименовывается в
        ``SKILL.md``, тогда как остальные файлы сохраняют свой относительный
        путь. Сопоставление по явному ключу (а не по позиции в списке)
        остаётся корректным независимо от этого переименования или порядка
        обхода директории.
        """

        def _key(skill: Skill, file: SkillFile) -> str:
            if same_path(file.path, skill.file_path):
                return ""
            return file.path.relative_to(skill.folder_path).as_posix()

        new_by_key = {_key(new_skill, f): f for f in new_skill.files}
        pairs = []
        for old_file in old_skill.files:
            new_file = new_by_key.get(_key(old_skill, old_file))
            if new_file is not None:
                pairs.append((old_file, new_file))
        return pairs

    def _should_exclude(
        self,
        link: absLink,
        skill: Skill,
        skill_file: SkillFile,
        other_skills: List[Skill],
    ) -> bool:
        """Return ``True`` if the link must not be rewritten.

        Mirrors the exclusions used by link validation so that the adapter
        never rewrites inline-code, web or skip-folder links.

        Возвращает ``True``, если ссылку не нужно переписывать. Повторяет
        исключения из валидации ссылок, чтобы адаптер не трогал ссылки в
        инлайн-коде, веб-ссылки и ссылки из пропускаемых директорий.
        """
        link_context = LinkWithContext.build(skill, skill_file, link)
        return any(
            rule.should_exclude(link_context, other_skills)
            for rule in self._exclude_rules
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
            content: Content of the copied file to rewrite.
                / Содержимое скопированного файла для перезаписи.
            links: Links found in the corresponding *source* file.
                / Ссылки, найденные в соответствующем *исходном* файле.
            skill_file: Source file that contains the links.
                / Исходный файл, содержащий ссылки.
            skill: Source skill that owns the file.
                / Исходный навык, которому принадлежит файл.
            other_skills: Other known source skills for resolving skill links.
                / Другие известные исходные навыки для разрешения ссылок на навыки.

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
            # Skip links excluded by validation rules (inline code, web links,
            # files inside skip folders).
            # Пропускаем ссылки, исключённые правилами валидации (инлайн-код,
            # веб-ссылки, файлы внутри пропускаемых директорий).
            if self._should_exclude(link, skill, skill_file, other_skills):
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
            link: Link to rewrite, parsed from the source file.
                / Ссылка для перезаписи, распарсенная из исходного файла.
            skill_file: Source file containing the link.
                / Исходный файл, содержащий ссылку.
            skill: Source skill that owns the file.
                / Исходный навык, которому принадлежит файл.
            other_skills: Other known source skills.
                / Другие известные исходные навыки.

        Returns:
            The new link target, or ``None`` if the link should be left unchanged
            (for example external URLs).
            Новая цель ссылки или ``None``, если ссылку следует оставить без
            изменений (например, внешние URL).
        """
        # Resolve the repo-absolute target via the dedicated converter. The
        # converter walks the *source* skill list to find the link's target
        # identity, then translates it into its current-run location via
        # skill_mapping. target_skill_folder/copied_files let links to files
        # outside any skill be copied into files/.
        # Разрешаем цель в формате repo-absolute через специализированный
        # конвертер. Конвертер обходит список *исходных* скиллов, чтобы найти
        # идентичность цели ссылки, затем переводит её в текущее расположение
        # через skill_mapping. target_skill_folder/copied_files позволяют
        # копировать в files/ ссылки на файлы вне любого скилла.
        new_skill = self._adapter_context.skill_mapping.get(skill, skill)
        return self._link_converter.convert(
            link,
            other_skills,
            self._adapter_context.skill_mapping,
            target_skill_folder=new_skill.folder_path,
            copied_files=self._adapter_context.copied_files,
            repo_path=self._adapter_context.repo_path,
        )
