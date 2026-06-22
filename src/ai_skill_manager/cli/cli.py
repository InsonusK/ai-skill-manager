"""Command-line interface.

Entry point for the ``ai-skill-manager`` / ``aism`` commands.
Registers subcommands from the ``commands`` package.

Точка входа для команд ``ai-skill-manager`` / ``aism``.
Регистрирует подкоманды из пакета ``commands``.
"""

import argparse

from .commands.discover.cli import add_parser as discover_add_parser
from .commands.new.cli import add_parser as new_add_parser
from .commands.sync.cli import add_parser as sync_add_parser


def main():
    """Run the main CLI entry point.

    Запускает основную точку входа CLI.
    """
    # EN: Create the top-level argument parser.
    # RU: Создаём корневой парсер аргументов.
    parser = argparse.ArgumentParser(
        prog='ai-skill-manager',
        description='AI skills manager CLI / CLI менеджера AI-навыков',
    )
    # EN: Require a subcommand; ``dest`` lets us know which one was chosen.
    # RU: Требуем подкоманду; ``dest`` позволяет узнать, какая выбрана.
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Register subcommand parsers.
    # Регистрируем парсеры подкоманд.
    sync_add_parser(subparsers)
    new_add_parser(subparsers)
    discover_add_parser(subparsers)

    # EN: Parse CLI arguments and dispatch to the selected subcommand.
    # RU: Парсим аргументы CLI и передаём управление выбранной подкоманде.
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
