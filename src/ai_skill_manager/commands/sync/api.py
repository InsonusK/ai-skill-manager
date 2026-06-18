"""Sync command API."""

from pathlib import Path
from typing import Optional

from ...core import SkillSync

DEFAULT_CONFIG = "ai-skills.yaml"


def run_sync(
    config_path: Path,
    target_dir: Optional[Path] = None,
    on_conflict: str = "error",
    remove_orphans: Optional[bool] = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """Run synchronization and return the result dictionary.

    Args:
        config_path: Path to the configuration file.
        target_dir: Optional override for the target directory.
        on_conflict: Conflict resolution strategy (``error`` or ``last_wins``).
        remove_orphans: Whether to remove orphan skills. Defaults to ``True``.
        dry_run: If ``True``, do not write any changes.
        force: If ``True``, skip hash and version checks.

    Returns:
        Result dictionary from ``SkillSync.sync()``.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
    """
    config_path = config_path.resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    sync = SkillSync(
        config_file=config_path,
        target_dir=target_dir,
        on_conflict=on_conflict,
        remove_orphans=remove_orphans if remove_orphans is not None else True,
        dry_run=dry_run,
        force=force,
    )
    return sync.sync()
