from enum import Enum


class LinkKind(Enum):
    os_absolute="os_absolute"
    """OS absolute path"""
    relative="relative"
    repo_absolute="repo_absolute"
    """Path from root of repository"""