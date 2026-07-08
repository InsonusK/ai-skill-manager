"""Core validator orchestration.

Aggregates validation rules and applies them to a list of skills,
producing a ``ValidationReport``.

Основная оркестрация валидации.

Агрегирует правила валидации и применяет их к списку навыков,
формируя ``ValidationReport``.
"""

import inspect
import logging
from typing import Optional, Tuple

from ..progress import ProgressCallback
from .models.validation_report import Skill, ValidationReport, Dict, ValidationResult
from .rules import absValidationRule, DEFAULT_RULES, List

# Module logger / Логгер модуля.
logger = logging.getLogger(__name__)


class Validator:
    """Orchestrates multiple validation rules against a list of skills.

    Ensures that registered rules have unique names and then runs each
    rule over the supplied skills, merging per-rule results into a single
    report.

    Оркестрирует несколько правил валидации для списка навыков.

    Гарантирует уникальность имён зарегистрированных правил, затем
    запускает каждое правило на переданных навыках, объединяя
    результаты по правилам в единый отчёт.
    """

    def __init__(self, rule_list: List[absValidationRule] = DEFAULT_RULES):
        """Initialize the validator with the given list of rules.

        Args:
            rule_list: List of validation rules to apply.
                / Список правил валидации для применения.

        Raises:
            AssertionError: If two rules share the same name.
                / Если два правила имеют одинаковое имя.
        """
        # Collect rule names to check for duplicates.
        # Собираем имена правил для проверки дубликатов.
        rule_names = [r.name for r in rule_list]
        assert len(rule_names) == len(set(rule_names)), "Rules must have unique names"
        self.__rules = rule_list

    @property
    def registered_rules_name_version(self) -> List[Tuple[str, str]]:
        """Return names and versions of all registered rules.

        Возвращает имена и версии всех зарегистрированных правил.
        """
        return [(rule.name, rule.version) for rule in self.__rules]

    def validate(
        self,
        skills: List[Skill],
        progress: Optional[ProgressCallback] = None,
    ) -> ValidationReport:
        """Validate all skills against every registered rule.

        Validates all skills against every registered rule and returns a
        merged ``ValidationReport``.

        Проверяет все навыки по всем зарегистрированным правилам и
        возвращает объединённый ``ValidationReport``.

        Args:
            skills: List of skills to validate.
                / Список навыков для валидации.
            progress: Optional ``(stage, current, total)`` callback for progress
                reporting. / Опциональный callback для отчёта о прогрессе.

        Returns:
            Aggregated validation report.
                / Агрегированный отчёт валидации.
        """
        # Map each skill to its rule-name -> ValidationResult mapping.
        # Сопоставляем каждому навыку отображение имя_правила -> ValidationResult.
        report_dict: Dict[Skill, Dict[absValidationRule, ValidationResult]] = {}

        logger.debug("Validating %d skill(s) with %d rule(s)", len(skills), len(self.__rules))
        if progress is not None:
            progress("validate", 0, len(self.__rules))

        for index, rule in enumerate(self.__rules, start=1):
            # Run the current rule against all skills.
            # Запускаем текущее правило для всех навыков.
            logger.debug("Running validation rule %d/%d: %s", index, len(self.__rules), rule.name)
            # Some custom rules may not accept the progress callback yet, so
            # fall back to the old signature when needed.
            # Некоторые пользовательские правила могут ещё не принимать callback
            # прогресса, поэтому при необходимости используем старую сигнатуру.
            if "progress" in inspect.signature(rule.validate).parameters:
                rule_report = rule.validate(skills, progress=progress)
            else:
                rule_report = rule.validate(skills)
            for skill, result in rule_report.items():
                # Get or create the per-skill result map.
                # Получаем или создаём карту результатов для навыка.
                skill_validation_results = report_dict.get(skill, {})

                # Store the result for the current rule.
                # Сохраняем результат текущего правила.
                skill_validation_results[rule] = result

                # Write the updated map back to the report.
                # Записываем обновлённую карту обратно в отчёт.
                report_dict[skill] = skill_validation_results

            if progress is not None:
                progress("validate", index, len(self.__rules))

        report = ValidationReport(report_dict)
        error_count = sum(len(rules) for rules in report.errors.values())
        logger.debug("Validation complete: %d error(s)", error_count)
        return report
