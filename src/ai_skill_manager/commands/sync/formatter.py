"""Sync command output formatter.

Converts the result dictionary from ``run_sync`` into a console-friendly
multi-line string.

Преобразует словарь результата от ``run_sync`` в удобную для консоли
многострочную строку.
"""

from typing import Any, Dict, List


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
