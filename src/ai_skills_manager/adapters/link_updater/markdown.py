"""Markdown link adapter."""

import os
from typing import Optional

from .base import Link, AdaptContext, AdaptResult, LinkTypeAdapter, find_source_dir_for_file, format_managed_link


class MarkdownLinkAdapter(LinkTypeAdapter):
    """Adapter for standard Markdown links: [text](url) and ![alt](url)."""

    def is_match(self, link: Link) -> bool:
        if link.link_type != 'markdown':
            return False
        # Skip external, anchor-only, absolute, and special protocols
        if link.target.startswith(('http://', 'https://', 'ftp://', 'mailto:', '#', '/')):
            return False
        return True

    def adapt(self, link: Link, context: AdaptContext) -> Optional[AdaptResult]:
        source_dir = find_source_dir_for_file(
            context.filepath, context.file_skill, context.mappings
        )
        if not source_dir:
            return None

        linked_source = (source_dir / link.target).resolve()

        # Managed file (in source_to_target map)
        if linked_source in context.source_to_target:
            new_target = context.source_to_target[linked_source]
            return format_managed_link(
                new_target, link.text, link.fragment, link.is_image, context
            )

        # External existing file
        if linked_source.exists():
            try:
                new_rel = os.path.relpath(
                    linked_source, context.filepath.parent
                ).replace(os.sep, "/")
                prefix = "!" if link.is_image else ""
                return AdaptResult(
                    text=f"{prefix}[{link.text}]({new_rel}{link.fragment})",
                    status="external",
                )
            except ValueError:
                return None

        # Broken link
        return None
