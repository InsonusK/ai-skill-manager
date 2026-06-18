"""Wiki link by name adapter."""

import logging
import os
from typing import Optional

from .base import Link, AdaptContext, AdaptResult, LinkTypeAdapter, format_managed_link

logger = logging.getLogger(__name__)


class WikiLinkByNameAdapter(LinkTypeAdapter):
    """Adapter for wiki links by file name: [[file name]]."""

    def is_match(self, link: Link) -> bool:
        if link.link_type != 'wiki':
            return False
        target = link.target
        return '/' not in target and not target.startswith('/')

    def adapt(self, link: Link, context: AdaptContext) -> Optional[AdaptResult]:
        target_name = link.target
        candidates = []

        for src_file in context.all_source_files:
            if src_file.name == target_name or src_file.name == target_name + '.md':
                candidates.append(src_file)
            elif src_file.name == 'SKILL.md' and src_file.parent.name == target_name:
                # Match skill entry points by folder name
                candidates.append(src_file)

        if len(candidates) == 1:
            target_file = context.source_to_target.get(candidates[0])
            if target_file:
                return format_managed_link(
                    target_file, link.text, link.fragment, False, context
                )
            # Exists but not in our map -> external (should not happen often)
            try:
                new_rel = os.path.relpath(
                    candidates[0], context.filepath.parent
                ).replace(os.sep, "/")
                return AdaptResult(
                    text=f"[{link.text}]({new_rel}{link.fragment})",
                    status="external",
                )
            except ValueError:
                return None

        if len(candidates) > 1:
            logger.warning(
                "Ambiguous wiki link [[%s]] in %s: %d matches found",
                target_name, context.filepath, len(candidates)
            )
            return None

        return None
