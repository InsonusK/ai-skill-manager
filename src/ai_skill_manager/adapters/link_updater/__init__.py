"""Updates links after skill sync using adapter pattern.

Rules:
- Links within same skill -> relative path (unchanged structure)
- Links to other managed skills -> skill link format [text](skill-name|uid: guid|#header)
- Links to external files -> relative path to new location
- Broken links -> left as-is, reported in validation

Supported link types:
- Markdown links: [text](url) and ![alt](url)
- Wiki links by name: [[file name]]
- Wiki links by absolute path: [[/abs/path]]
- Wiki links by relative path: [[rel/path]]

Wiki links may include optional header and custom name:
- [[file#header|custom name]] -> [custom name](skill-name|uid: guid|#header)
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

from ai_skill_manager.discovery.base import SkillMapping

from .base import (
    AdaptContext,
    AdaptResult,
    Link,
    LinkTypeAdapter,
    SkillInfo,
    parse_skill_info,
)
from .markdown import MarkdownLinkAdapter
from .wiki_absolute import WikiLinkByAbsolutePathAdapter
from .wiki_name import WikiLinkByNameAdapter
from .wiki_relative import WikiLinkByRelativePathAdapter

logger = logging.getLogger(__name__)

MD_LINK_RE = re.compile(r'!?\[([^\]]*)\]\(([^\s\)"]*)\)')
WIKI_LINK_RE = re.compile(r'\[\[([^\]]+)\]\]')

__all__ = [
    "AdaptContext",
    "AdaptResult",
    "Link",
    "LinkTypeAdapter",
    "LinkUpdater",
    "MarkdownLinkAdapter",
    "SkillInfo",
    "WikiLinkByAbsolutePathAdapter",
    "WikiLinkByNameAdapter",
    "WikiLinkByRelativePathAdapter",
    "parse_skill_info",
]


class LinkUpdater:
    """Main link updater that registers and orchestrates all link adapters."""

    @property
    def version(self) -> int:
        return 2

    def __init__(
        self,
        mappings: List[SkillMapping],
        source_to_target: dict[Path, Path],
        all_source_files: set[Path],
        dry_run: bool = False,
    ):
        self.mappings = {m.skill_name: m for m in mappings}
        self.source_to_target = source_to_target
        self.all_source_files = all_source_files
        self.dry_run = dry_run
        self.fixes: List[dict] = []

        # Build skill registries
        self.skill_infos: dict[str, SkillInfo] = {}
        self.source_to_skill: dict[Path, SkillInfo] = {}
        self.target_to_skill: dict[Path, SkillInfo] = {}

        for mapping in mappings:
            skill_info = parse_skill_info(mapping)
            if skill_info:
                self.skill_infos[mapping.skill_name] = skill_info

        # Map each source file to its skill
        for src_file in all_source_files:
            for mapping in mappings:
                skill_info = self.skill_infos.get(mapping.skill_name)
                if not skill_info:
                    continue
                if mapping.is_flat:
                    if src_file == mapping.source_path:
                        self.source_to_skill[src_file] = skill_info
                        break
                else:
                    try:
                        src_file.relative_to(mapping.source_path)
                        self.source_to_skill[src_file] = skill_info
                        break
                    except ValueError:
                        continue

        # Map each target file to its skill via source_to_target
        for src_file, target_file in source_to_target.items():
            skill_info = self.source_to_skill.get(src_file)
            if skill_info:
                self.target_to_skill[target_file] = skill_info

        # Register adapters
        self.adapters: List[LinkTypeAdapter] = [
            MarkdownLinkAdapter(),
            WikiLinkByNameAdapter(),
            WikiLinkByAbsolutePathAdapter(),
            WikiLinkByRelativePathAdapter(),
        ]

    def _find_skill_for_file(self, filepath: Path) -> Optional[SkillInfo]:
        """Find skill info for a target file."""
        # Direct lookup from source_to_target mapping
        skill_info = self.target_to_skill.get(filepath)
        if skill_info:
            return skill_info

        # Fallback: infer from target path structure
        for mapping in self.mappings.values():
            skill_info = self.skill_infos.get(mapping.skill_name)
            if not skill_info:
                continue
            if mapping.is_flat:
                if filepath == mapping.target_path / 'SKILL.md':
                    return skill_info
            else:
                try:
                    filepath.relative_to(mapping.target_path)
                    return skill_info
                except ValueError:
                    continue

        return None

    def _parse_links(self, content: str) -> List[tuple[int, Link]]:
        """Parse all links from content, returning list of (position, Link)."""
        links: List[tuple[int, Link]] = []

        # Markdown links
        for match in MD_LINK_RE.finditer(content):
            full = match.group(0)
            text = match.group(1)
            path = match.group(2)
            is_image = full.startswith('!')

            # Skip pure anchor links and empty links
            if not path or path.startswith('#'):
                continue

            if '#' in path:
                path_clean, fragment = path.split('#', 1)
                fragment = f"#{fragment}"
            else:
                path_clean = path
                fragment = ""

            links.append((match.start(), Link(
                full_match=full,
                link_type='markdown',
                text=text,
                target=path_clean,
                fragment=fragment,
                is_image=is_image,
            )))

        # Wiki links
        for match in WIKI_LINK_RE.finditer(content):
            full = match.group(0)
            inner = match.group(1)

            # Parse wiki syntax: target#fragment|text or target|text or target#fragment or target
            if '|' in inner:
                left, custom_text = inner.rsplit('|', 1)
            else:
                left = inner
                custom_text = None

            if '#' in left:
                target, fragment = left.split('#', 1)
                fragment = f"#{fragment}"
            else:
                target = left
                fragment = ""

            display_text = custom_text if custom_text is not None else Path(target).name

            links.append((match.start(), Link(
                full_match=full,
                link_type='wiki',
                text=display_text,
                target=target,
                fragment=fragment,
                is_image=False,
            )))

        links.sort(key=lambda x: x[0])
        return links

    def _replace_link(self, link: Link, context: AdaptContext) -> str:
        """Find matching adapter and adapt the link."""
        matching = [a for a in self.adapters if a.is_match(link)]

        if len(matching) == 0:
            # No adapter claimed this link (e.g. external URL, anchor-only)
            return link.full_match

        if len(matching) > 1:
            logger.warning(
                "Link %s in %s matches multiple adapters (%s), leaving unchanged",
                link.full_match, context.filepath,
                ', '.join(a.__class__.__name__ for a in matching)
            )
            self.fixes.append({
                "file": str(context.filepath),
                "old": link.full_match,
                "status": "broken",
                "reason": "ambiguous link type (matches multiple adapters)",
            })
            return link.full_match

        adapter = matching[0]
        result = adapter.adapt(link, context)

        if result is None:
            self.fixes.append({
                "file": str(context.filepath),
                "old": link.full_match,
                "status": "broken",
                "reason": "target file does not exist",
            })
            return link.full_match

        self.fixes.append({
            "file": str(context.filepath),
            "old": link.full_match,
            "new": result.text,
            "status": result.status,
        })
        return result.text

    def adapt(self, filepath: Path) -> None:
        """Update links in a single markdown file."""
        if not filepath.exists() or filepath.suffix != ".md":
            return

        content = filepath.read_text(encoding="utf-8")
        original = content

        file_skill = self._find_skill_for_file(filepath)

        context = AdaptContext(
            filepath=filepath,
            file_skill=file_skill,
            source_to_target=self.source_to_target,
            all_source_files=self.all_source_files,
            target_to_skill=self.target_to_skill,
            source_to_skill=self.source_to_skill,
            mappings=self.mappings,
        )

        links = self._parse_links(content)

        if not links:
            return

        parts: List[str] = []
        last_end = 0

        for pos, link in links:
            parts.append(content[last_end:pos])
            replacement = self._replace_link(link, context)
            parts.append(replacement)
            last_end = pos + len(link.full_match)

        parts.append(content[last_end:])
        new_content = ''.join(parts)

        if new_content != original and not self.dry_run:
            filepath.write_text(new_content, encoding="utf-8")

    def adapt_all(self, target_dir: Path) -> List[dict]:
        """Update links in all markdown files under target_dir."""
        self.fixes = []
        if not target_dir.exists():
            return self.fixes

        for md_file in target_dir.rglob("*.md"):
            self.adapt(md_file)

        return self.fixes
