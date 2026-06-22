"""Utility functions for ai-skills."""

import hashlib
import json
from pathlib import Path
from typing import Optional
from .entities import Skill
MANAGER_TAG_FILE = ".ai-skills-managed"

def compute_skill_hash(skill: Skill) -> str:
    """Compute hash of a skill source."""
    if skill.is_flat():
        return compute_hash(skill.file_path)
    h = hashlib.sha256()
    for file_path in sorted([f.path for f in skill.files]):
        if file_path.is_file():
            rel = str(file_path.relative_to(skill.folder_path))
            h.update(rel.encode())
            h.update(compute_hash(file_path).encode())
    return h.hexdigest()

def compute_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def is_managed(skill_dir: Path) -> bool:
    """Check if directory was created by this tool."""
    return (skill_dir / MANAGER_TAG_FILE).exists()


def tag_managed(skill_dir: Path) -> None:
    """Mark directory as managed by this tool."""
    (skill_dir / MANAGER_TAG_FILE).touch()


def read_managed_state(skill_dir: Path) -> Optional[dict]:
    """Read managed state from skill directory."""
    path = skill_dir / MANAGER_TAG_FILE
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def write_managed_state(skill_dir: Path, state: dict) -> None:
    """Write managed state to skill directory."""
    path = skill_dir / MANAGER_TAG_FILE
    path.write_text(json.dumps(state, indent=2), encoding='utf-8')
