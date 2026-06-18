"""Discover command CLI."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from ...config import load_config
from ...core import STRATEGIES
from ...discovery.base import SkillMapping
from .api import (
    DEFAULT_CONFIG,
    DEFAULT_TARGET,
    discover_from_config,
    discover_single_source,
    resolve_target,
)
from .formatter import format_mappings


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "discover",
        help="Discover skills and print mappings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help=f"Config file (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=list(STRATEGIES.keys()),
        help="Discovery strategy for a single source",
    )
    parser.add_argument("-p", "--path", help="Source path or GitHub repo URL")
    parser.add_argument(
        "--target",
        help=f"Override target directory (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--tree",
        default="master",
        help="Git tree/branch when type=github (default: master)",
    )
    parser.add_argument(
        "--subpath",
        action="append",
        default=None,
        help="GitHub subpath when type=github (can be repeated; default: skills)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.set_defaults(func=run)
    return parser


def _discover(args) -> List[SkillMapping]:
    if args.config:
        config_path = Path(args.config).resolve()
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        target_dir = resolve_target(
            config_path.parent,
            load_config(config_path).get("settings", {}),
            args.target,
        )
        return discover_from_config(config_path, target_dir)

    if args.type:
        target_dir = (
            Path(args.target).resolve()
            if args.target
            else Path(DEFAULT_TARGET).resolve()
        )
        return discover_single_source(
            args.type,
            args.path,
            target_dir,
            tree=args.tree,
            subpath=args.subpath,
        )

    config_path = Path(DEFAULT_CONFIG).resolve()
    if config_path.exists():
        target_dir = resolve_target(
            config_path.parent,
            load_config(config_path).get("settings", {}),
            args.target,
        )
        return discover_from_config(config_path, target_dir)

    raise ValueError(
        "No config file specified and no source type provided.\n"
        "   Use --config <file> or --type <auto|directory|flat|github> --path <source>"
    )


def run(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    try:
        mappings = _discover(args)
        print(format_mappings(mappings))
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
