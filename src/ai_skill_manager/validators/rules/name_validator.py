"""Validation rule that checks skill names against file/folder names.

Ensures the skill name declared in the front matter matches the file or
folder name for each supported skill format.

Правило валидации, проверяющее имя навыка на соответствие имени файла
или папки.

Гарантирует, что имя навыка, указанное в метаданных, совпадает с именем
файла или папки для каждого поддерживаемого формата навыка.
"""

import re
from typing import Dict, Optional
from .abs_validation_rule import Skill, absValidationRule, ValidationResult, List
from ...entities import SkillFormat
from ...progress import ProgressCallback
from ..models import ValidationSeverity, ValidationError


class NameValidationRule(absValidationRule):
    """Validates that a skill's declared name matches its file system name."""
    @property
    def version(self) -> str:
        """Return the rule version. / Возвращает версию правила."""
        return "1.0.0"

    def validate(
        self,
        skills: List[Skill],
        progress: Optional[ProgressCallback] = None,
    ) -> Dict[Skill, ValidationResult]:
        """Validate each skill's name depending on its format.

        Проверяет имя каждого навыка в зависимости от его формата.

        Args:
            skills: Skills to validate.
                / Навыки для валидации.
            progress: Optional ``(stage, current, total)`` callback for progress
                reporting. / Опциональный callback для отчёта о прогрессе.

        Returns:
            Per-skill validation results.
                / Результаты валидации по каждому навыку.
        """
        results = {}
        for skill in skills:
            # A skill must declare a name in its header properties.
            # Навык должен объявлять имя в свойствах заголовка.
            if skill.properties.name is None:
                results[skill] = ValidationResult.single(
                    ValidationError(
                        "Name is not set in properties", ValidationSeverity.ERROR)
                )
                continue

            # Dispatch validation based on the skill format.
            # Направляем валидацию в зависимости от формата навыка.
            if skill.format == SkillFormat.Agent:
                if len((errors := self.__validate_agent(skill))) > 0:
                    results[skill] = ValidationResult(tuple(errors))
            elif skill.format == SkillFormat.HumanFlat:
                if len((errors := self.__validate_human_flat(skill))) > 0:
                    results[skill] = ValidationResult(tuple(errors))
            elif skill.format == SkillFormat.HumanDir:
                # Directory skills must satisfy both flat-like and directory checks.
                # Навыки-директории должны удовлетворять как flat-проверкам, так и проверкам директории.
                errors = []
                if len((new_errors := self.__validate_human_flat(skill))) > 0:
                    errors.extend(new_errors)
                if len((new_errors := self.__validate_human_dir(skill))) > 0:
                    errors.extend(new_errors)
                if len(errors) > 0:
                    results[skill] = ValidationResult(errors)
            else:
                # Unknown format should never reach here; fail loudly if it does.
                # Неизвестный формат не должен сюда попадать; если попал — выбрасываем ошибку.
                raise ValueError(f"Unknown skill format {skill.format}")
        return results

    def __validate_human_dir(self, skill: Skill) -> List[ValidationError]:
        """Validate a directory-based human skill name.

        Проверяет имя навыка в формате директории.

        Returns:
            A validation error if the folder name is invalid, otherwise ``None``.
                / Ошибка валидации, если имя папки некорректно, иначе ``None``.
        """
        folder_name = skill.folder_path.name

        # Human directory skills must live in a ``*.skill`` folder.
        # Навыки-директории human должны находиться в папке ``*.skill``.
        if not folder_name.endswith(".skill"):
            return [ValidationError(
                "Skill folder name doesn't ends on '.skill'",
                ValidationSeverity.ERROR,
            )]

        errors = []
        # Compare the folder name without the ``.skill`` suffix to the declared name.
        # Сравниваем имя папки без суффикса ``.skill`` с объявленным именем.
        skill_name = folder_name[:-6]
        if skill_name != skill.properties.name:
            errors.append(
                ValidationError(
                    "Skill folder name ({folder_name}) != skill name in header properties ({skill_name})",
                    ValidationSeverity.ERROR,
                    {
                        "folder_name": skill.folder_path.name,
                        "skill_name": skill.properties.name,
                    },
                )
            )
        if not NameValidationRule.is_kebab_case(skill_name):
            errors.append(
                ValidationError(
                    "Skill folder name ({folder_name}) is not in kebab case",
                    ValidationSeverity.ERROR,
                    {
                        "folder_name": skill.folder_path.name
                    },
                )
            )
        if not NameValidationRule.is_kebab_case(skill.properties.name):
            errors.append(
                ValidationError(
                    "Skill name ({skill_name}) is not in kebab case",
                    ValidationSeverity.ERROR,
                    {
                        "skill_name": skill.properties.name,
                    },
                )
            )
        return errors

    def __validate_human_flat(self, skill: Skill) -> List[ValidationError]:
        """Validate a flat human skill file name.

        Проверяет имя файла плоского human-навыка.

        Returns:
            A validation error if the file name is invalid, otherwise ``None``.
                / Ошибка валидации, если имя файла некорректно, иначе ``None``.
        """
        file_name = skill.file_path.name

        # Flat human skills must use the ``.skill.md`` extension.
        # Плоские human-навыки должны использовать расширение ``.skill.md``.
        if not file_name.endswith(".skill.md"):
            return [ValidationError(
                "Skill file name doesn't ends on '.skill.md'",
                ValidationSeverity.ERROR,
            )]

        errors = []
        # Compare the file name without the ``.skill.md`` suffix to the declared name.
        # Сравниваем имя файла без суффикса ``.skill.md`` с объявленным именем.
        skill_name = file_name[:-9]
        if skill_name != skill.properties.name:
            errors.append(
                ValidationError(
                    "Skill file name ({file_name}) != skill name in header properties ({skill_name})",
                    ValidationSeverity.ERROR,
                    {
                        "file_name": skill.file_path.name,
                        "skill_name": skill.properties.name,
                    },
                )
            )
        if not NameValidationRule.is_kebab_case(skill_name):
            errors.append(
                ValidationError(
                    "Skill file name ({file_name}) is not in kebab case",
                    ValidationSeverity.ERROR,
                    {
                        "file_name": skill.file_path.name
                    },
                )
            )
        if not NameValidationRule.is_kebab_case(skill.properties.name):
            errors.append(
                ValidationError(
                    "Skill name ({skill_name}) is not in kebab case",
                    ValidationSeverity.ERROR,
                    {
                        "skill_name": skill.properties.name,
                    },
                )
            )
        return errors

    def __validate_agent(self, skill: Skill) -> List[ValidationError]:
        """Validate an agent skill folder name.

        Проверяет имя папки навыка-агента.

        Returns:
            A validation error if the folder name does not match, otherwise ``None``.
                / Ошибка валидации, если имя папки не совпадает, иначе ``None``.
        """
        errors = []
        if skill.folder_path.name != skill.properties.name:
            errors.append(
                ValidationError(
                    "Folder name ({folder_name}) != skill name in header properties ({skill_name})",
                    ValidationSeverity.ERROR,
                    {
                        "folder_name": skill.folder_path.name,
                        "skill_name": skill.properties.name,
                    },
                )
            )
        if not NameValidationRule.is_kebab_case(skill.folder_path.name):
            errors.append(
                ValidationError(
                    "Folder name ({folder_name}) is not in kebab case",
                    ValidationSeverity.ERROR,
                    {
                        "folder_name": skill.folder_path.name
                    },
                )
            )
        if not NameValidationRule.is_kebab_case(skill.properties.name):
            errors.append(
                ValidationError(
                    "Skill name ({skill_name}) is not in kebab case",
                    ValidationSeverity.ERROR,
                    {
                        "skill_name": skill.properties.name,
                    },
                )
            )
        return errors

    @staticmethod
    def is_kebab_case(name: str) -> bool:
        if not name or \
                name.startswith("-") or name.endswith("-") or "--" in name or \
                not re.match(r'^[a-z0-9-]+$', name) or not re.match(r'^[a-z0-9]', name):
            return False
        return True
