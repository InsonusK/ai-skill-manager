"""Sync command CLI."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .api import DEFAULT_CONFIG, run_sync
from .formatter import format_sync_result


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "sync",
        help="Sync AI skills into .agents/skills/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--config",
        default=DEFAULT_CONFIG,
        help=f"Config file (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument("--target", help="Override target directory")
    parser.add_argument(
        "--on-conflict",
        choices=["error", "last_wins"],
        help="Conflict resolution",
    )
    parser.add_argument(
        "--remove-orphans",
        action="store_true",
        default=None,
        help="Remove orphan skills",
    )
    parser.add_argument(
        "--keep-orphans",
        action="store_true",
        help="Keep orphan skills",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force copy all skills, skip hash and version checks",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.set_defaults(func=run)
    return parser


def run(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    config_path = Path(args.config).resolve()

    remove: Optional[bool] = None
    if args.remove_orphans:
        remove = True
    elif args.keep_orphans:
        remove = False

    try:
        result = run_sync(
            config_path=config_path,
            target_dir=Path(args.target) if args.target else None,
            on_conflict=args.on_conflict or "error",
            remove_orphans=remove if remove is not None else True,
            dry_run=args.dry_run,
            force=args.force,
        )
        print(format_sync_result(result))
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
