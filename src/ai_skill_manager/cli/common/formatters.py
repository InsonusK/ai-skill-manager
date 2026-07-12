"""CLI output formatters.

Converts command results into human-readable terminal output. Rich console
rendering stays in the CLI layer.

Форматёры вывода CLI.
Преобразуют результаты команд в читаемый терминальный вывод. Рендеринг
через Rich остаётся в слое CLI.
"""

from typing import Any, Dict, List

from rich.console import Console
from rich.text import Text
from rich.tree import Tree

from ...adapters.models.sync_error import SyncError
from ...entities.skill import Skill
from ...entities.source import Source
from ...sync_exception import SyncFailedError


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


def print_sync_errors(error: SyncFailedError) -> None:
    """Print materialization failures collected during a sync run.

    Печатает ошибки материализации, собранные во время синхронизации.

    Args:
        error: The raised sync failure, carrying the collected errors and
            the staging/target paths.
            / Возникшая ошибка синхронизации, содержащая собранные ошибки и
            пути staging/target.
    """
    console = Console()
    tree = Tree(f"[bold red]Sync Failed[/bold red] ({len(error.errors)} error(s))")
    by_skill: Dict[str, List[SyncError]] = {}
    for sync_error in error.errors:
        by_skill.setdefault(sync_error.skill_name, []).append(sync_error)

    for skill_name, skill_errors in by_skill.items():
        skill_branch = tree.add(f"[cyan]{skill_name}[/cyan]")
        for sync_error in skill_errors:
            text = Text(
                sync_error.file and f"{sync_error.file}: {sync_error.message}" or sync_error.message,
                style="red",
            )
            skill_branch.add(text)

    console.print(tree)
    console.print(f"\n[bold]{error.target_dir}[/bold] was left unchanged.")
    console.print(f"Inspect the staged output at [bold]{error.staging_dir}[/bold].")
