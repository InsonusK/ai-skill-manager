"""Link replacement in markdown files.

Finds all links in a file, dispatches each one through the mapper, writes
a copy of the file with updated links, and returns the copy path together
with the list of performed fixes.
"""

import logging
from pathlib import Path
from typing import List, Optional

from .models.link import Link
from .service.LinkFactory import LinkFactory

from .base import LinkContext, ReplaceResult, SkillInfo, parse_skill_info
from .models.file_context import FileContext as FileContextModel
from .map import LinkMapError, LinkMapper
from ...models.source import LocalSource

logger = logging.getLogger(__name__)


class LinkReplacer:
    """Replaces links in a markdown file using a mapper."""

    def __init__(self, mapper: Optional[LinkMapper] = None):
        self.mapper = mapper or LinkMapper()

    def replace(self, context: LinkContext) -> ReplaceResult:
        """Create a copy of ``context.filepath`` with links updated.

        Args:
            context: Link adaptation context.

        Returns:
            A ``ReplaceResult`` containing the path to the new file and the
            list of fixes that were performed or recorded.
        """
        filepath = context.filepath
        content = filepath.read_text(encoding="utf-8")
        factory = LinkFactory()
        links = factory.create_links(
            FileContextModel(path=filepath, skill=context.skill, content=content)
        )

        parts: List[str] = []
        last_end = 0
        fixes: List[dict] = []

        for link in links:
            pos = link.context.start
            end = link.context.end

            parts.append(content[last_end:pos])

            if self._is_skipped(link):
                parts.append(link.full)
                last_end = end
                continue

            try:
                replacement = self.mapper.map(link, context)
                status = "fixed"
                reason: Optional[str] = None
            except (LinkMapError, RuntimeError) as exc:
                replacement = link.full
                status = "broken"
                reason = str(exc)
                logger.warning(
                    "Link %s in %s left unchanged: %s",
                    link.full, filepath, reason
                )

            parts.append(replacement)
            last_end = end

            fix: dict = {"file": str(filepath), "old": link.full, "status": status}
            if reason:
                fix["reason"] = reason
            if status == "fixed":
                fix["new"] = replacement
            fixes.append(fix)

        parts.append(content[last_end:])
        new_content = "".join(parts)

        new_path = filepath.with_suffix(filepath.suffix + ".link_update")
        new_path.write_text(new_content, encoding="utf-8")

        return ReplaceResult(new_path=new_path, fixes=fixes)

    def replace_skill(self, skill) -> List[ReplaceResult]:
        """Replace links in all ``*.md`` files of a single skill.

        The context (repo root, skill registries) is built from
        ``skill.source``. For local sources the repo root is the source path
        and links are resolved against all skills discovered in that path.

        Args:
            skill: The skill whose markdown files should be processed.

        Returns:
            A list of ``ReplaceResult``, one for each markdown file in the
            skill.

        Raises:
            NotImplementedError: If the skill source is not a ``LocalSource``.
        """
        if not isinstance(skill.source, LocalSource):
            raise NotImplementedError(
                f"replace_skill is only implemented for LocalSource, got {skill.source.source_type}"
            )

        # Local import to avoid a circular dependency at module load time.
        from ...discovery.source.auto import AutoDiscovery

        repo_root = skill.source.path.resolve()
        all_skills = AutoDiscovery(repo_root).discover()

        skill_infos: dict[str, SkillInfo] = {}
        source_to_skill: dict[Path, SkillInfo] = {}
        all_source_files: set[Path] = set()

        for discovered in all_skills:
            info = parse_skill_info(discovered)
            if not info:
                continue
            target_path = repo_root / info.name
            skill_infos[info.name] = SkillInfo(
                name=info.name,
                uid=info.uid,
                target_path=target_path,
                source_path=info.source_path,
                is_flat=info.is_flat,
            )
            files = self._collect_files(discovered)
            all_source_files.update(files)
            for file_path in files:
                source_to_skill[file_path] = skill_infos[info.name]

        # Identity mapping: we are editing files in-place in the source tree.
        source_to_target = {f: f for f in all_source_files}
        target_to_source = source_to_target
        target_to_skill = source_to_skill

        results: List[ReplaceResult] = []
        for file_path in sorted(self._collect_files(skill)):
            if file_path.suffix != ".md":
                continue

            file_context = FileContextModel(path=file_path, skill=skill)
            link_context = LinkContext(
                skill=file_context.skill,
                filepath=file_path,
                file_skill=source_to_skill.get(file_path),
                repo_root=repo_root,
                skills=skill_infos,
                source_to_target=source_to_target,
                target_to_source=target_to_source,
                all_source_files=all_source_files,
                target_to_skill=target_to_skill,
                source_to_skill=source_to_skill,
            )
            results.append(self.replace(link_context))

        return results

    def _collect_files(self, skill) -> set[Path]:
        """Return all file paths belonging to a skill."""
        if skill.is_flat():
            return {skill.file_path}
        return {p for p in skill.folder_path.rglob("*") if p.is_file()}

    def _is_skipped(self, link: Link) -> bool:
        """Return True for links that should be left untouched."""
        if link.kind != "markdown":
            return False
        target = link.target
        return (
            not target
            or target.startswith("#")
            or target.startswith(("http://", "https://", "ftp://", "mailto:"))
        )
