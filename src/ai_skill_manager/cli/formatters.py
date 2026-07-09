"""CLI output formatters.

Converts command results and validation reports into human-readable terminal
output. Rich console rendering stays in the CLI layer.

Форматёры вывода CLI.
Преобразуют результаты команд и отчёты валидации в читаемый терминальный
вывод. Рендеринг через Rich остаётся в слое CLI.
"""

from typing import Any, Dict, List

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from ..entities.skill import Skill
from ..entities.source import Source
from ..validators.models import ValidationReport
from ..validators.rules import absValidationRule


def format_sync_result(result: Dict[str, Any]) -> str:
    """Format sync result dictionary as console output.

    Форматирует словарь результата синхронизации для вывода в консоль.

    Args:
        result: Dictionary returned by ``run_sync``. / Словарь, возвращённый ``run_sync``.

    Returns:
        Multi-line formatted string. / Многострочная отформатированная строка.
    """
    lines = []

    # Prefer the service-level field, fall back to legacy synced_count.
    # Предпочитаем поле сервиса, с запасным вариантом из legacy synced_count.
    synced_count = result.get("skills_count", result.get("synced_count", 0))
    lines.append(f"\n📊 Synced: {synced_count} skills")

    if result.get("skipped_count", 0) > 0:
        lines.append(f"   ⏭️  skipped: {result['skipped_count']}")

    links_replaced = result.get("links_replaced")
    if links_replaced:
        lines.append(f"\n🔗 Links replaced: {links_replaced}")

    # Legacy fix_summary support (kept for backward compatibility).
    # Поддержка устаревшего fix_summary (для обратной совместимости).
    fix_summary = result.get("fix_summary", {})
    if fix_summary:
        lines.append("\n🔗 Links:")
        for status, count in sorted(fix_summary.items()):
            emoji = {"fixed": "✅", "external": "🔗", "broken": "⚠️"}.get(
                status, "?"
            )
            lines.append(f"   {emoji} {status}: {count}")

    broken_fixes: List[Dict[str, Any]] = [
        f for f in result.get("fixes", []) if f.get("status") == "broken"
    ]
    if broken_fixes:
        lines.append("\n⚠️  Broken links:")
        for fix in broken_fixes:
            lines.append(f"   • {fix['file']}")
            lines.append(f"     Link: {fix['old']}")
            if "reason" in fix:
                lines.append(f"     Reason: {fix['reason']}")

    if result.get("dry_run"):
        lines.append("\n🏃 Dry run - no changes")

    return "\n".join(lines)


def format_skills(skills: List[Skill]) -> str:
    """Format a list of Skill objects as a tree grouped by source.

    Returns a plain string representation. When no skills are discovered a
    simple message is returned.

    Args:
        skills: Discovered skills. / Обнаруженные навыки.

    Returns:
        Formatted string. / Отформатированная строка.
    """
    if not skills:
        return "No skills discovered."

    lines = ["Discovered skills"]
    source_reports: Dict[Source, List[Skill]] = {}
    for skill in skills:
        source_report = source_reports.get(skill.source, [])
        source_report.append(skill)
        source_reports[skill.source] = source_report

    for source, source_skills in source_reports.items():
        lines.append(f"  {source}")
        for skill in source_skills:
            name = skill.name or "(unnamed)"
            lines.append(f"    {name}")
            for skill_file in skill.files:
                rel_path = skill_file.path.relative_to(skill.source_path)
                lines.append(f"      {rel_path}")

    lines.append(f"\nTotal: {len(skills)} skill(s)")
    return "\n".join(lines)


def print_skills(skills: List[Skill]) -> None:
    """Print a list of Skill objects as a rich tree grouped by source.

    Args:
        skills: Discovered skills. / Обнаруженные навыки.
    """
    if not skills:
        print("No skills discovered.")
        return

    console = Console()
    tree = Tree("[bold]Discovered skills[/bold]")

    source_reports: Dict[Source, List[Skill]] = {}
    for skill in skills:
        source_report = source_reports.get(skill.source, [])
        source_report.append(skill)
        source_reports[skill.source] = source_report

    for source, source_skills in source_reports.items():
        source_branch = tree.add(f"[cyan]{source}[/cyan]")
        for skill in source_skills:
            name = skill.name or "(unnamed)"
            skill_branch = source_branch.add(f"{name}")
            for skill_file in skill.files:
                rel_path = skill_file.path.relative_to(skill.source_path)
                skill_branch.add(str(rel_path))

    console.print(tree)
    console.print(f"\nTotal: {len(skills)} skill(s)")


def format_validation_report(report: ValidationReport) -> str:
    """Format a validation report as a plain string.

    Args:
        report: Validation report. / Отчёт о валидации.

    Returns:
        Formatted report string. / Отформатированный отчёт.
    """
    lines = ["Validation Failed"]
    for skill, rule_errors in report.result.items():
        lines.append(f"  {skill.source}")
        lines.append(f"    {skill.name}")
        lines.append(f"    {skill.file_path}")
        for rule, result in rule_errors.items():
            lines.append(
                f"      {rule.name} {rule.version}: {len(result.errors)} error(s)"
            )
            for error in result.errors:
                lines.append(f"        {error}")

    total = sum(
        len(r.errors) for s in report.result.values() for r in s.values()
    )
    lines.append(f"\nTotal: {total} error(s)")
    return "\n".join(lines)


def print_validation_report(report: ValidationReport) -> None:
    """Print a validation report as a rich tree.

    Args:
        report: Validation report. / Отчёт о валидации.
    """
    console = Console()
    tree = Tree("[bold red]Validation Failed[/bold red]")
    source_reports: Dict[Source, Dict[Skill, Dict[absValidationRule, Any]]] = {}
    for skill, rule_errors in report.result.items():
        source_report: Dict[Skill, Dict[absValidationRule, Any]] = source_reports.get(
            skill.source, {}
        )
        source_report[skill] = rule_errors
        source_reports[skill.source] = source_report

    for source, source_report in source_reports.items():
        source_branch = tree.add(f"[cyan]{source}")
        for skill, rule_errors in source_report.items():
            skill_branch = source_branch.add(f"{skill.name}\n{skill.file_path}")
            for rule, result in rule_errors.items():
                rule_branch = skill_branch.add(
                    f"[green]{rule.name} {rule.version}[/green]: "
                    f"{len(result.errors)} error(s)"
                )
                for error in result.errors:
                    text = Text(str(error), style="red")
                    rule_branch.add(text)
    console.print(tree)
    total = sum(
        len(r.errors) for s in report.result.values() for r in s.values()
    )
    console.print(f"\nTotal: {total} error(s)")
