"""Skill discovery strategies."""

from .auto import AutoDiscovery
from .DiscoveryStrategy import DiscoveryStrategy
from .github import GitHubDiscovery

__all__ = [
    "DiscoveryStrategy",
    "AutoDiscovery",
    "GitHubDiscovery",
]
