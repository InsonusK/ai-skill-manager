"""CLI package for ai-skill-manager.

Provides the ``main`` entry point used by the ``ai-skill-manager`` / ``aism``
console scripts.

Пакет CLI для ai-skill-manager.
Предоставляет точку входа ``main``, используемую консольными скриптами
``ai-skill-manager`` / ``aism``.
"""

import argparse
import logging
import sys

from ..profiling import profile_command

from .sync import add_parser as sync_add_parser

__all__ = ["main"]


def _configure_logging(debug: bool) -> None:
    """Set up root logging for the CLI.

    Включает корневое логирование для CLI.
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        force=True,
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog='ai-skill-manager',
        description='AI skills manager CLI / CLI менеджера AI-навыков',
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging / Включить отладочное логирование",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable profiling and print top calls by time / "
             "Включить профилирование и вывести самые затратные вызовы",
    )
    parser.add_argument(
        "--profile-output",
        metavar="FILE",
        default="ai-skill-manager.prof",
        help="Raw profiling dump file (default: ai-skill-manager.prof) / "
             "Файл для сохранения сырых данных профилирования",
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    sync_add_parser(subparsers)

    return parser


def main():
    """Run the main CLI entry point.

    Запускает основную точку входа CLI.
    """
    # Ensure stdout/stderr use UTF-8 so emoji and non-ASCII characters in
    # formatter output do not crash on Windows with legacy code pages.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = _build_parser()
    args = parser.parse_args()

    _configure_logging(getattr(args, "debug", False))

    logger = logging.getLogger(__name__)
    logger.debug("Starting command: %s", args.command)

    try:
        exit_code = profile_command(args.func)(args)
    except SystemExit as e:
        raise
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
        sys.exit(1)

    logger.debug("Command finished with exit code: %s", exit_code)
    sys.exit(exit_code if exit_code is not None else 0)
