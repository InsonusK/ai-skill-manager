"""Validation rule for links inside skills.

Правило валидации ссылок внутри скиллов.
"""

from typing import Callable, Dict, List, Optional

from ....entities import PathLink, Skill
from ....models import LinkWithContext
from ....progress import ProgressCallback
from ...models import ValidationError, ValidationResult, ValidationSeverity
from ..abs_validation_rule import absValidationRule
from .exclude_rule import build_link_exclude_rules, absExcludeRule


class LinkValidationRule(absValidationRule):
    """Validate that every link points to an existing target and, when the
    target belongs to a skill, that the skill is included in the current sync.

    Проверяет, что каждая ссылка ведёт на существующую цель и, когда цель
    принадлежит скиллу, что этот скилл входит в текущее копирование.
    """

    def __init__(self, exclude_rules: Optional[List[absExcludeRule]] = None):
        """Initialize the rule with optional exclude rules.

        Args:
            exclude_rules: Rules that decide which links are skipped. When
                ``None``, the default set (inline-code, web links, skip folders)
                is used.
                / Правила, определяющие, какие ссылки пропускаются. При
                ``None`` используется набор по умолчанию (инлайн-код,
                веб-ссылки, пропускаемые директории).
        """
        self.__exclude_rules = (
            exclude_rules if exclude_rules is not None else build_link_exclude_rules()
        )

    @property
    def version(self) -> str:
        """Return the rule version. / Возвращает версию правила."""
        return "1.2.0"

    def validate(
        self,
        skills: List[Skill],
        progress: Optional[ProgressCallback] = None,
    ) -> Dict[Skill, ValidationResult]:
        """Validate links for all provided skills.

        Валидирует ссылки для всех переданных скиллов.

        Args:
            skills: Skills to validate.
                / Навыки для валидации.
            progress: Optional ``(stage, current, total)`` callback for progress
                reporting. / Опциональный callback для отчёта о прогрессе.

        Returns:
            Per-skill validation results.
                / Результаты валидации по каждому навыку.
        """
        results: Dict[Skill, ValidationResult] = {}

        # Count the total number of links so the progress bar has a meaningful
        # upper bound.
        # Считаем общее количество ссылок, чтобы у прогресс-бара было
        # осмысленное максимальное значение.
        total_links = sum(
            len(skill_file.links)
            for skill in skills
            for skill_file in skill.files
        )
        if progress is not None:
            progress("link_validation", 0, total_links)

        processed_links = 0

        def _report_one() -> None:
            """Report that one more link has been processed."""
            nonlocal processed_links
            processed_links += 1
            if progress is not None:
                progress("link_validation", processed_links, total_links)

        for skill in skills:
            # Collect all link errors for the current skill.
            # Собираем все ошибки ссылок для текущего навыка.
            errors = self._validate_skill(skill, skills, _report_one)
            if errors:
                results[skill] = ValidationResult(errors)

        if progress is not None:
            progress("link_validation", processed_links, total_links)

        return results

    def _validate_skill(
        self,
        skill: Skill,
        skills: List[Skill],
        report_one: Callable[[], None],
    ) -> List[ValidationError]:
        """Validate all links inside ``skill``.

        Валидирует все ссылки внутри ``skill``.

        Args:
            skill: Skill whose links are being checked.
                / Навык, ссылки которого проверяются.
            skills: All known skills, used to resolve inter-skill links.
                / Все известные навыки, используемые для разрешения межнавыковых ссылок.
            report_one: Callback invoked after each processed link.
                / Callback, вызываемый после обработки каждой ссылки.

        Returns:
            List of validation errors found in the skill.
                / Список найденных ошибок валидации в навыке.
        """
        errors: List[ValidationError] = []

        # Iterate over every file that belongs to the skill.
        # Перебираем каждый файл, принадлежащий навыку.
        for skill_file in skill.files:
            for link in skill_file.links:
                # Build the link context so we can inspect its target.
                # Формируем контекст ссылки, чтобы можно было проверить её цель.
                link_context = LinkWithContext.build(skill, skill_file, link)

                # Apply exclude rules first.
                # Сначала применяем правила исключения.
                if any(
                    rule.should_exclude(link_context, skills)
                    for rule in self.__exclude_rules
                ):
                    report_one()
                    continue

                if (error := self.__validate_link(link_context, skills)) is not None:
                    errors.append(error)

                report_one()
        return errors

    def __validate_link(self, link: LinkWithContext, skills: List[Skill]) -> Optional[ValidationError]:
        """Validate a single link context.

        Проверяет один контекст ссылки.

        Args:
            link: Link context to validate.
                / Контекст ссылки для проверки.
            skills: All known skills.
                / Все известные навыки.

        Returns:
            A validation error if the link is invalid, otherwise ``None``.
                / Ошибка валидации, если ссылка некорректна, иначе ``None``.
        """
        # Path links must point to an existing file.
        # Путевые ссылки должны указывать на существующий файл.
        if isinstance(link.base, PathLink) and not link.base.path.exists:
            return ValidationError(
                message="Link {link_raw}\nPath {link}\nFile {file}\nPos ({start}-{end}): target file does not exist",
                severity=ValidationSeverity.ERROR,
                params={
                    "link_raw": link.base.raw,
                    "link": link.base.path.formatted,
                    "file": link.context.file.path.relative_to(link.context.skill.file_path.parent),
                    "start": link.base.start,
                    "end": link.base.end,
                },
            )

        # Links that point to a file inside the same skill are valid.
        # Ссылки, указывающие на файл внутри того же навыка, считаются корректными.
        if link.is_link_to_skill_file:
            return None

        # Links that point to another known skill are valid.
        # Ссылки, указывающие на другой известный навык, считаются корректными.
        if link.is_link_to_another_skill(skills) is not None:
            return None

        # Links that point to another known file in skill are valid.
        # Ссылки, указывающие на другой известный файл в навыке, считаются корректными.
        if link.is_link_to_another_skill_file(skills) is not None:
            return None

        # Links to files inside another skill that is part of the current sync
        # set are valid. This includes non-markdown files such as implementation
        # templates, which are not listed as skill files but are still copied
        # together with the skill.
        # Ссылки на файлы внутри другого скилла, входящего в текущее копирование,
        # считаются корректными. Это включает не-markdown файлы, например шаблоны
        # реализации, которые не являются skill-файлами, но копируются вместе со
        # скиллом.
        target_skill = link.target_skill(skills)
        if target_skill is not None:
            return None

        # Anything else (source or OS file) is allowed as long as the file exists.
        # Всё остальное (source- или OS-файл) разрешено, пока файл существует.
        return None
