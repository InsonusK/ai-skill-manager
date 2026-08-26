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
from pathlib import Path
from typing import List, Optional

from ..config import LoggingSettings, load_config, parse_logging_settings
from ..profiling import profile_command

from .common.source_parser import DEFAULT_CONFIG
from .sync import add_parser as sync_add_parser

__all__ = ["main"]


def _configure_logging(logging_settings: LoggingSettings) -> None:
    """Set up root logging for the CLI.

    Включает корневое логирование для CLI.
    """
    level = getattr(logging, logging_settings.level.upper())
    handlers: List[logging.Handler] = [logging.StreamHandler()]

    log_file = logging_settings.to_file
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, mode="a"))

    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        handlers=handlers,
        force=True,
    )


def _resolve_config_path(args) -> Optional[Path]:
    """Resolve the config file path from CLI arguments without loading it.

    Mirrors the resolution order of ``build_sources_from_args``:
    1. Explicit ``--config``.
    2. Default config file in the current directory (only when no direct
       source arguments are given).
    3. ``None`` when running in direct source mode.
    """
    config = getattr(args, "config", None)
    if config:
        return Path(config).resolve()

    # Direct source mode does not use a config file.
    if getattr(args, "type", None):
        return None

    default_path = Path(DEFAULT_CONFIG).resolve()
    if default_path.exists():
        return default_path

    return None


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

    config_path = _resolve_config_path(args)
    config_base: Optional[Path] = None
    if config_path is not None and config_path.exists():
        config = load_config(config_path)
        settings = config.get("settings", {})
        logging_settings = parse_logging_settings(settings)
        config_base = config_path.parent
    else:
        logging_settings = LoggingSettings()

    if getattr(args, "debug", False):
        logging_settings = LoggingSettings(
            level="debug",
            to_file=logging_settings.to_file,
        )

    log_file = logging_settings.to_file
    if log_file is not None and not log_file.is_absolute() and config_base is not None:
        log_file = config_base / log_file

    _configure_logging(
        LoggingSettings(level=logging_settings.level, to_file=log_file)
    )

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
