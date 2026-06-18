"""Command-line interface."""

import argparse

from .commands.discover.cli import add_parser as discover_add_parser
from .commands.new.cli import add_parser as new_add_parser
from .commands.sync.cli import add_parser as sync_add_parser


def main():
    parser = argparse.ArgumentParser(
        prog='ai-skill-manager',
        description='AI skills manager CLI',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    sync_add_parser(subparsers)
    new_add_parser(subparsers)
    discover_add_parser(subparsers)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
