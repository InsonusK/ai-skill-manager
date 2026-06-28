"""Validation rule for links inside skills.

Правило валидации ссылок внутри скиллов.
"""

from typing import Dict, List, Optional

from ...entities import PathLink, Skill, WebLink
from ...models import LinkWithContext
from ..models import ValidationError, ValidationResult, ValidationSeverity
from .abs_validation_rule import absValidationRule


class LinkValidationRule(absValidationRule):
    """Validate that every link points to an existing target and, when the
    target belongs to a skill, that the skill is included in the current sync.

    Проверяет, что каждая ссылка ведёт на существующую цель и, когда цель
    принадлежит скиллу, что этот скилл входит в текущее копирование.
    """

    @property
    def version(self) -> str:
        """Return the rule version. / Возвращает версию правила."""
        return "1.1.0"

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

        # Links to files that belong to a skill outside the current sync set are
        # not allowed. If a target lies inside a skill directory but that skill
        # is not in the provided list, report an error.
        # Ссылки на файлы скилла, который не входит в текущее копирование,
        # запрещены. Если цель лежит внутри директории скилла, но этот скилл
        # отсутствует в переданном списке, сообщаем об ошибке.
        target_skill = link.target_skill(skills)
        if target_skill is not None and target_skill is not link.context.skill:
            return ValidationError(
                message="Link {link_raw}\nPath {link}\nFile {file}\nPos ({start}-{end}): target belongs to skill '{target_skill}' which is not included in the current sync",
                severity=ValidationSeverity.ERROR,
                params={
                    "link_raw": link.base.raw,
                    "link": link.base.path.formatted,
                    "file": link.context.file.path.relative_to(link.context.skill.file_path.parent),
                    "target_skill": target_skill.properties.name or target_skill.file_path.as_posix(),
                    "start": link.base.start,
                    "end": link.base.end,
                },
            )

        # Anything else (source or OS file) is allowed as long as the file exists.
        # Всё остальное (source- или OS-файл) разрешено, пока файл существует.
        return None
