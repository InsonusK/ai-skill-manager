"""Validation rule for links inside skills.

Правило валидации ссылок внутри скиллов.
"""

from typing import Dict, List, Optional

from ...entities import PathLink, Skill, WebLink
from ...models import LinkWithContext
from ..models import ValidationError, ValidationResult, ValidationSeverity
from .abs_validation_rule import absValidationRule


class LinkValidationRule(absValidationRule):
    """Validate that every link points to another skill or inside its own skill.

    Проверяет, что каждая ссылка ведёт либо на другой скилл, либо на файл
    внутри своей директории скилла.
    """

    @property
    def version(self) -> str:
        """Return the rule version. / Возвращает версию правила."""
        return "1.0.0"

    def validate(self, skills: List[Skill]) -> Dict[Skill, ValidationResult]:
        """Validate links for all provided skills.

        Валидирует ссылки для всех переданных скиллов.

        Args:
            skills: Skills to validate.
                / Навыки для валидации.

        Returns:
            Per-skill validation results.
                / Результаты валидации по каждому навыку.
        """
        results: Dict[Skill, ValidationResult] = {}
        for skill in skills:
            # Collect all link errors for the current skill.
            # Собираем все ошибки ссылок для текущего навыка.
            errors = self._validate_skill(skill, skills)
            if errors:
                results[skill] = ValidationResult(errors)
        return results

    def _validate_skill(self, skill: Skill, skills: List[Skill]) -> List[ValidationError]:
        """Validate all links inside ``skill``.

        Валидирует все ссылки внутри ``skill``.

        Args:
            skill: Skill whose links are being checked.
                / Навык, ссылки которого проверяются.
            skills: All known skills, used to resolve inter-skill links.
                / Все известные навыки, используемые для разрешения межнавыковых ссылок.

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

                if (error := self.__validate_link(link_context, skills)) is not None:
                    errors.append(error)
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
        # External web links are always allowed.
        # Внешние веб-ссылки всегда разрешены.
        if isinstance(link.base, WebLink):
            return None

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

        # Anything else is a dangling link.
        # Всё остальное — висячая ссылка.
        return ValidationError(
            message="Link {link_raw}\nPath {link}\nFile {file}\nRepos {repo}\nPos ({start}-{end}): doesn't lead to subfiles or other skills",
            severity=ValidationSeverity.ERROR,
            params={
                "link_raw": link.base.raw,
                "repo": link.context.skill.source.get_scan_location().repo_path,
                "link": link.base.path.formatted,
                "file": link.context.file.path.relative_to(link.context.skill.file_path.parent),
                "start": link.base.start,
                "end": link.base.end
            },
        )
