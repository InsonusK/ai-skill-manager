"""Command-line interface entry point.

Allows running the application directly with ``python ai_skill_manager/cli.py``.
The real entry point lives in :mod:`ai_skill_manager.cli`.

Точка входа командной строки.
Позволяет запускать приложение напрямую через ``python ai_skill_manager/cli.py``.
Реальная точка входа находится в :mod:`ai_skill_manager.cli`.
"""

from ai_skill_manager.cli import main

if __name__ == "__main__":
    main()
