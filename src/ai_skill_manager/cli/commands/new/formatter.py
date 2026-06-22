"""New skill output formatter.

Formats API results as human-readable console messages.
Форматирует результаты API в понятные сообщения для консоли.
"""

from pathlib import Path


def format_created(path: Path, is_flat: bool) -> str:
    """Format a success message for a created skill.

    Формирует сообщение об успешном создании навыка.

    Args:
        path: Path returned by ``create_skill``. / Путь, возвращённый ``create_skill``.
        is_flat: ``True`` for flat skills, ``False`` for directory skills.
            / ``True`` для плоских навыков, ``False`` для навыков-директорий.

    Returns:
        Localized success message. / Локализованное сообщение об успехе.

    Example:
        >>> format_created(Path("skills/hello"), False)
        '✅ Created directory skill: skills/hello'
    """
    kind = "flat skill" if is_flat else "directory skill"
    return f"✅ Created {kind}: {path}"
