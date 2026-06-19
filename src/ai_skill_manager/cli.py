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
    parser = argparse.ArgumentParser(
        prog='ai-skill-manager',
        description='AI skills manager CLI / CLI менеджера AI-навыков',
    )
    subparsers:argparse._SubParsersAction[argparse.ArgumentParser] = parser.add_subparsers(dest='command', required=True)

    # Register subcommand parsers.
    # Регистрируем парсеры подкоманд.
    sync_add_parser(subparsers)
    new_add_parser(subparsers)
    discover_add_parser(subparsers)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
