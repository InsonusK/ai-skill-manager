"""Allow running the CLI package as a module.

Usage: python -m ai_skill_manager.cli <subcommand> ...

Позволяет запускать пакет CLI как модуль.
Использование: python -m ai_skill_manager.cli <подкоманда> ...
"""

from . import main

if __name__ == "__main__":
    main()
