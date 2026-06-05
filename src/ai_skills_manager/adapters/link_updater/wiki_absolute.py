"""Wiki link by absolute path adapter."""

import os
from pathlib import Path
from typing import Optional

from .base import Link, AdaptContext, AdaptResult, LinkTypeAdapter, format_managed_link


class WikiLinkByAbsolutePathAdapter(LinkTypeAdapter):
    """Adapter for wiki links with absolute paths: [[/abs/path]]."""

    def is_match(self, link: Link) -> bool:
        if link.link_type != 'wiki':
            return False
        return link.target.startswith('/')

    def adapt(self, link: Link, context: AdaptContext) -> Optional[AdaptResult]:
        target_path = Path(link.target).resolve()

        # Try exact match first
        for src_file in context.all_source_files:
            if src_file.resolve() == target_path:
                target_file = context.source_to_target.get(src_file)
                if target_file:
                    return format_managed_link(
                        target_file, link.text, link.fragment, False, context
                    )
                try:
                    new_rel = os.path.relpath(
                        src_file, context.filepath.parent
                    ).replace(os.sep, "/")
                    return AdaptResult(
                        text=f"[{link.text}]({new_rel}{link.fragment})",
                        status="external",
                    )
                except ValueError:
                    return None

        # Try with .md appended
        target_path_md = Path(str(target_path) + '.md')
        for src_file in context.all_source_files:
            if src_file.resolve() == target_path_md:
                target_file = context.source_to_target.get(src_file)
                if target_file:
                    return format_managed_link(
                        target_file, link.text, link.fragment, False, context
                    )

        return None
