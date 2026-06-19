"""Wiki link by relative path adapter."""

import os
from pathlib import Path
from typing import Optional

from .base import Link, AdaptContext, AdaptResult, LinkTypeAdapter, find_source_dir_for_file, format_managed_link


class WikiLinkByRelativePathAdapter(LinkTypeAdapter):
    """Adapter for wiki links with relative paths: [[rel/path]]."""

    def is_match(self, link: Link) -> bool:
        if link.link_type != 'wiki':
            return False
        target = link.target
        return '/' in target and not target.startswith('/')

    def adapt(self, link: Link, context: AdaptContext) -> Optional[AdaptResult]:
        source_dir = find_source_dir_for_file(
            context.filepath, context.file_skill, context.skills
        )
        if not source_dir:
            return None

        resolved = (source_dir / link.target).resolve()

        if resolved in context.all_source_files:
            target_file = context.source_to_target.get(resolved)
            if target_file:
                return format_managed_link(
                    target_file, link.text, link.fragment, False, context
                )
            try:
                new_rel = os.path.relpath(
                    resolved, context.filepath.parent
                ).replace(os.sep, "/")
                return AdaptResult(
                    text=f"[{link.text}]({new_rel}{link.fragment})",
                    status="external",
                )
            except ValueError:
                return None

        # Try with .md appended
        resolved_md = Path(str(resolved) + '.md')
        if resolved_md in context.all_source_files:
            target_file = context.source_to_target.get(resolved_md)
            if target_file:
                return format_managed_link(
                    target_file, link.text, link.fragment, False, context
                )
            try:
                new_rel = os.path.relpath(
                    resolved_md, context.filepath.parent
                ).replace(os.sep, "/")
                return AdaptResult(
                    text=f"[{link.text}]({new_rel}{link.fragment})",
                    status="external",
                )
            except ValueError:
                return None

        return None
