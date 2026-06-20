"""Tests for LinkUpdater adapter."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.adapters.link_updater import LinkUpdater
from ai_skill_manager.adapters.link_updater.models.Link import Link, LinkLocation
from ai_skill_manager.adapters.link_updater.base import FileContext, LinkContext, SkillInfo
from ai_skill_manager.adapters.link_updater.map import LinkMapError, LinkMapper
from ai_skill_manager.adapters.link_updater.replace import LinkReplacer
from ai_skill_manager.adapters.link_updater.service.LinkFactory import LinkFactory
from ai_skill_manager.adapters.link_updater.rules import (
    MarkdawnRelativeRule,
    WikilinkAbsoluteRule,
    WikilinkRelativeRule,
)
from ai_skill_manager.models import LocalSource, Skill


def _derive_name(file_path: Path) -> str:
    if file_path.name.endswith(".skill.md"):
        return file_path.name[:-9]
    return file_path.stem


def _skill(file_path: Path, folder_path: Path | None = None) -> Skill:
    """Create a Skill and ensure its markdown file has a frontmatter name."""
    name = folder_path.name if folder_path else _derive_name(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    original = ""
    if file_path.exists():
        original = file_path.read_text()
        if not original.startswith("---"):
            original = f"---\nname: {name}\n---\n{original}"
    else:
        original = f"---\nname: {name}\n---\n"
    file_path.write_text(original)
    return Skill(
        file_path=file_path,
        folder_path=folder_path,
        source=LocalSource(folder_path if folder_path else file_path.parent),
    )


class TestLinkUpdater(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.target = self.tmpdir / "target"
        self.target.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_no_links(self):
        md = self.target / "guide.md"
        md.write_text("# Guide\nNo links here.")

        updater = LinkUpdater([], self.target, {}, set())
        updater.adapt(md)

        content = md.read_text()
        self.assertEqual(content, "# Guide\nNo links here.")
        self.assertEqual(len(updater.fixes), 0)

    def test_external_link_unchanged(self):
        md = self.target / "guide.md"
        md.write_text("# Guide\nSee [example](https://example.com).")

        updater = LinkUpdater([], self.target, {}, set())
        updater.adapt(md)

        content = md.read_text()
        self.assertIn("https://example.com", content)
        self.assertEqual(len(updater.fixes), 0)

    def test_anchor_link_unchanged(self):
        md = self.target / "guide.md"
        md.write_text("# Guide\nSee [section](#section).")

        updater = LinkUpdater([], self.target, {}, set())
        updater.adapt(md)

        content = md.read_text()
        self.assertIn("#section", content)
        self.assertEqual(len(updater.fixes), 0)

    def test_absolute_markdown_link_is_broken(self):
        """Absolute Markdown paths are not a supported link format."""
        md = self.target / "guide.md"
        md.write_text("# Guide\nSee [root](/etc/passwd).")

        updater = LinkUpdater([], self.target, {}, set())
        updater.adapt(md)

        content = md.read_text()
        self.assertIn("/etc/passwd", content)
        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)
        self.assertIn("no matching rule", broken[0]["reason"])

    def test_fix_managed_link_cross_skill(self):
        """Link to a file in another skill becomes a skill link."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [other](./other.md).")
        source_other = source_dir / "other.md"
        source_other.write_text("# Other")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [other](./other.md).")

        target_other = self.target / "other" / "SKILL.md"
        target_other.parent.mkdir()
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide)
        other_skill = _skill(source_other)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }

        updater = LinkUpdater(
            [guide_skill, other_skill],
            self.target,
            source_to_target,
            {source_guide, source_other},
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("./other.md", content)
        self.assertIn("[other](skill: other)", content)

        fixes = [f for f in updater.fixes if f["status"] == "fixed"]
        self.assertEqual(len(fixes), 1)
        self.assertEqual(fixes[0]["old"], "[other](./other.md)")

    def test_dry_run_no_changes(self):
        """Dry run should not modify files but record fixes."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [other](./other.md).")
        source_other = source_dir / "other.md"
        source_other.write_text("# Other")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [other](./other.md).")

        target_other = self.target / "other" / "SKILL.md"
        target_other.parent.mkdir()
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide)
        other_skill = _skill(source_other)

        source_to_target = {source_guide: target_guide, source_other: target_other}

        updater = LinkUpdater(
            [guide_skill, other_skill],
            self.target,
            source_to_target,
            {source_guide, source_other},
            dry_run=True,
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("./other.md", content)

        self.assertEqual(len(updater.fixes), 1)
        self.assertEqual(updater.fixes[0]["status"], "fixed")

    def test_broken_link(self):
        """Link to non-existent file is marked broken."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [missing](./missing.md).")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [missing](./missing.md).")

        guide_skill = _skill(source_guide)

        updater = LinkUpdater([guide_skill], self.target, {}, {source_guide})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("./missing.md", content)

        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)

    def test_external_existing_file_is_broken(self):
        """Links to files outside managed skills are forbidden."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [ext](./external.md).")

        external = source_dir / "external.md"
        external.write_text("# External")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [ext](./external.md).")

        guide_skill = _skill(source_guide)

        updater = LinkUpdater([guide_skill], self.target, {}, {source_guide})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("./external.md", content)

        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)

    def test_adapt_all_recursive(self):
        """adapt_all processes all .md files recursively."""
        sub = self.target / "sub"
        sub.mkdir()

        md1 = self.target / "a.md"
        md1.write_text("# A")

        md2 = sub / "b.md"
        md2.write_text("# B")

        updater = LinkUpdater([], self.target, {}, set())
        updater.adapt_all(self.target)

        self.assertEqual(len(updater.fixes), 0)

    def test_image_link(self):
        """Image links are rewritten to relative target paths."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\n![img](./img.png)")
        source_img = source_dir / "img.png"
        source_img.write_text("png")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\n![img](./img.png)")

        target_img = self.target / "img.png"
        target_img.write_text("png")

        guide_skill = _skill(source_guide)

        source_to_target = {source_guide: target_guide, source_img: target_img}

        updater = LinkUpdater(
            [guide_skill],
            self.target,
            source_to_target,
            {source_guide, source_img},
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("](./img.png)", content)
        self.assertIn("](../img.png)", content)
        self.assertIn("![img](", content)

    def test_link_with_fragment_cross_skill(self):
        """Links with URL fragments to other skills use skill link format."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [other](./other.md#section).")
        source_other = source_dir / "other.md"
        source_other.write_text("# Other")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [other](./other.md#section).")

        target_other = self.target / "other" / "SKILL.md"
        target_other.parent.mkdir()
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide)
        other_skill = _skill(source_other)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }

        updater = LinkUpdater(
            [guide_skill, other_skill],
            self.target,
            source_to_target,
            {source_guide, source_other},
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("./other.md#section", content)
        self.assertIn("[other](skill: other#section)", content)

        fixes = [f for f in updater.fixes if f["status"] == "fixed"]
        self.assertEqual(len(fixes), 1)
        self.assertEqual(fixes[0]["old"], "[other](./other.md#section)")

    def test_external_link_with_fragment_is_broken(self):
        """External file links with fragments are forbidden."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [ext](./external.md#section).")

        external = source_dir / "external.md"
        external.write_text("# External")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [ext](./external.md#section).")

        guide_skill = _skill(source_guide)

        updater = LinkUpdater([guide_skill], self.target, {}, {source_guide})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("./external.md#section", content)

        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)

    def test_broken_link_with_fragment(self):
        """Broken links with fragments should still be reported as broken."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [missing](./missing.md#section).")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [missing](./missing.md#section).")

        guide_skill = _skill(source_guide)

        updater = LinkUpdater([guide_skill], self.target, {}, {source_guide})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("./missing.md#section", content)

        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)
        self.assertIn("target file does not exist", broken[0]["reason"])

    def test_markdown_link_same_skill(self):
        """Markdown link within same skill stays relative."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [other](./other.md).")
        source_other = source_dir / "other.md"
        source_other.write_text("# Other")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True, exist_ok=True)
        target_guide.write_text("# Guide\nSee [other](./other.md).")

        target_other = self.target / "guide" / "other.md"
        target_other.parent.mkdir(parents=True, exist_ok=True)
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }

        updater = LinkUpdater(
            [guide_skill],
            self.target,
            source_to_target,
            {source_guide, source_other},
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("./other.md", content)
        self.assertIn("[other](other.md)", content)

    def test_wiki_link_by_name_same_skill_is_broken(self):
        """Plain wiki links by file name are forbidden."""
        source_dir = self.tmpdir / "source" / "guide"
        source_dir.mkdir(parents=True)
        source_guide = source_dir / "SKILL.md"
        source_guide.write_text("# Guide\nSee [[other]].")
        source_other = source_dir / "other.md"
        source_other.write_text("# Other")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True, exist_ok=True)
        target_guide.write_text("# Guide\nSee [[other]].")

        target_other = self.target / "guide" / "other.md"
        target_other.parent.mkdir(parents=True, exist_ok=True)
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide, source_guide.parent)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater(
            [guide_skill],
            self.target,
            source_to_target,
            all_source_files,
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("[[other]]", content)
        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)
        self.assertIn("no matching rule", broken[0]["reason"])

    def test_wiki_link_by_name_cross_skill_is_broken(self):
        """Plain wiki links to another skill are forbidden."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()

        source_guide = source_dir / "guide" / "SKILL.md"
        source_guide.parent.mkdir(parents=True)
        source_guide.write_text("# Guide\nSee [[other]].")

        source_other = source_dir / "other" / "SKILL.md"
        source_other.parent.mkdir(parents=True)
        source_other.write_text("# Other")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True)
        target_guide.write_text("# Guide\nSee [[other]].")

        target_other = self.target / "other" / "SKILL.md"
        target_other.parent.mkdir(parents=True)
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide, source_guide.parent)
        other_skill = _skill(source_other, source_other.parent)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater(
            [guide_skill, other_skill],
            self.target,
            source_to_target,
            all_source_files,
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("[[other]]", content)
        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)

    def test_wiki_link_with_header_and_custom_text_is_broken(self):
        """Plain wiki links with headers/custom text are still forbidden."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()

        source_guide = source_dir / "guide" / "SKILL.md"
        source_guide.parent.mkdir(parents=True)
        source_guide.write_text('# Guide\nSee [[other#section|Custom Name]].')

        source_other = source_dir / "other" / "SKILL.md"
        source_other.parent.mkdir(parents=True)
        source_other.write_text("# Other")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True)
        target_guide.write_text('# Guide\nSee [[other#section|Custom Name]].')

        target_other = self.target / "other" / "SKILL.md"
        target_other.parent.mkdir(parents=True)
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide, source_guide.parent)
        other_skill = _skill(source_other, source_other.parent)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater(
            [guide_skill, other_skill],
            self.target,
            source_to_target,
            all_source_files,
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("[[other#section|Custom Name]]", content)
        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)

    def test_wiki_link_by_relative_path(self):
        """Wiki link with relative path resolves correctly."""
        source_dir = self.tmpdir / "source" / "guide"
        source_dir.mkdir(parents=True)
        source_guide = source_dir / "SKILL.md"
        source_guide.write_text("# Guide\nSee [[../other/SKILL.md]].")

        source_other = self.tmpdir / "source" / "other" / "SKILL.md"
        source_other.parent.mkdir(parents=True)
        source_other.write_text("# Other")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True)
        target_guide.write_text("# Guide\nSee [[../other/SKILL.md]].")

        target_other = self.target / "other" / "SKILL.md"
        target_other.parent.mkdir(parents=True)
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide, source_guide.parent)
        other_skill = _skill(source_other, source_other.parent)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater(
            [guide_skill, other_skill],
            self.target,
            source_to_target,
            all_source_files,
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("[[../other/SKILL.md]]", content)
        self.assertIn("[SKILL.md](skill: other)", content)

    def test_wiki_link_by_absolute_path(self):
        """Wiki link with absolute path from repo root resolves correctly."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()

        source_other = source_dir / "other" / "SKILL.md"
        source_other.parent.mkdir(parents=True)
        source_other.write_text("# Other")

        source_guide = source_dir / "guide" / "SKILL.md"
        source_guide.parent.mkdir(parents=True)
        source_guide.write_text("# Guide\nSee [[other/SKILL.md]].")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True)
        target_guide.write_text("# Guide\nSee [[other/SKILL.md]].")

        target_other = self.target / "other" / "SKILL.md"
        target_other.parent.mkdir(parents=True)
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide, source_guide.parent)
        other_skill = _skill(source_other, source_other.parent)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater(
            [guide_skill, other_skill],
            self.target,
            source_to_target,
            all_source_files,
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("[[other/SKILL.md]]", content)
        self.assertIn("[SKILL.md](skill: other)", content)

    def test_wiki_link_ambiguous_name_is_broken(self):
        """Plain wiki links matching multiple files are forbidden."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()

        source_guide = source_dir / "guide" / "SKILL.md"
        source_guide.parent.mkdir(parents=True)
        source_guide.write_text("# Guide\nSee [[common.md]].")

        source_common1 = source_dir / "guide" / "common.md"
        source_common1.write_text("# Common 1")

        source_common2 = source_dir / "other" / "common.md"
        source_common2.parent.mkdir(parents=True)
        source_common2.write_text("# Common 2")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True)
        target_guide.write_text("# Guide\nSee [[common.md]].")

        guide_skill = _skill(source_guide, source_guide.parent)

        source_to_target = {source_guide: target_guide}
        all_source_files = {source_guide, source_common1, source_common2}

        updater = LinkUpdater(
            [guide_skill],
            self.target,
            source_to_target,
            all_source_files,
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("[[common.md]]", content)

        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)
        self.assertIn("no matching rule", broken[0]["reason"])

    def test_wiki_link_broken(self):
        """Wiki link to non-existent file is marked broken."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()

        source_guide = source_dir / "guide" / "SKILL.md"
        source_guide.parent.mkdir(parents=True)
        source_guide.write_text("# Guide\nSee [[missing]].")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True)
        target_guide.write_text("# Guide\nSee [[missing]].")

        guide_skill = _skill(source_guide, source_guide.parent)

        updater = LinkUpdater([guide_skill], self.target, {}, {source_guide})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("[[missing]]", content)

        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)

    def test_wiki_link_same_skill_with_header_is_broken(self):
        """Plain wiki links with headers within same skill are forbidden."""
        source_dir = self.tmpdir / "source" / "guide"
        source_dir.mkdir(parents=True)
        source_guide = source_dir / "SKILL.md"
        source_guide.write_text("# Guide\nSee [[other#section]].")
        source_other = source_dir / "other.md"
        source_other.write_text("# Other")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True, exist_ok=True)
        target_guide.write_text("# Guide\nSee [[other#section]].")

        target_other = self.target / "guide" / "other.md"
        target_other.parent.mkdir(parents=True, exist_ok=True)
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide, source_guide.parent)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater(
            [guide_skill],
            self.target,
            source_to_target,
            all_source_files,
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("[[other#section]]", content)
        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)

    def test_wiki_link_by_name_with_custom_text_same_skill_is_broken(self):
        """Plain wiki links with custom text are forbidden."""
        source_dir = self.tmpdir / "source" / "guide"
        source_dir.mkdir(parents=True)
        source_guide = source_dir / "SKILL.md"
        source_guide.write_text("# Guide\nSee [[other|My Other File]].")
        source_other = source_dir / "other.md"
        source_other.write_text("# Other")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True, exist_ok=True)
        target_guide.write_text("# Guide\nSee [[other|My Other File]].")

        target_other = self.target / "guide" / "other.md"
        target_other.parent.mkdir(parents=True, exist_ok=True)
        target_other.write_text("# Other")

        guide_skill = _skill(source_guide, source_guide.parent)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater(
            [guide_skill],
            self.target,
            source_to_target,
            all_source_files,
        )
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("[[other|My Other File]]", content)
        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)


class TestLinkFactory(unittest.TestCase):
    def test_creates_markdown_link(self):
        factory = LinkFactory(filepath=Path("/tmp/guide/SKILL.md"))
        links = factory.create_links("See [text](./file.md#section).")

        self.assertEqual(len(links), 1)
        link = links[0]
        self.assertEqual(link.raw, "[text](./file.md#section)")
        self.assertEqual(link.full, "[text](./file.md#section)")
        self.assertEqual(link.path, "./file.md")
        self.assertEqual(link.target, "./file.md")
        self.assertEqual(link.text, "text")
        self.assertEqual(link.kind, "markdown")
        self.assertEqual(link.fragment, "#section")
        self.assertFalse(link.is_image)
        self.assertEqual(link.context.filepath, Path("/tmp/guide/SKILL.md"))
        self.assertEqual(link.context.start, 4)
        self.assertEqual(link.context.end, 29)

    def test_creates_wiki_link_with_custom_text(self):
        factory = LinkFactory(filepath=Path("/tmp/guide/SKILL.md"))
        links = factory.create_links("See [[../other/SKILL.md|Other Skill]].")

        self.assertEqual(len(links), 1)
        link = links[0]
        self.assertEqual(link.raw, "[[../other/SKILL.md|Other Skill]]")
        self.assertEqual(link.path, "../other/SKILL.md")
        self.assertEqual(link.text, "Other Skill")
        self.assertEqual(link.kind, "wiki")
        self.assertEqual(link.fragment, "")
        self.assertFalse(link.is_image)

    def test_creates_image_link(self):
        factory = LinkFactory(filepath=Path("/tmp/guide/SKILL.md"))
        links = factory.create_links("![alt](./img.png)")

        self.assertEqual(len(links), 1)
        link = links[0]
        self.assertEqual(link.raw, "![alt](./img.png)")
        self.assertEqual(link.path, "./img.png")
        self.assertEqual(link.text, "alt")
        self.assertTrue(link.is_image)

    def test_returns_links_in_source_order(self):
        factory = LinkFactory(filepath=Path("/tmp/guide/SKILL.md"))
        links = factory.create_links("[a](./a.md) [[b]] [c](./c.md)")

        self.assertEqual(len(links), 3)
        self.assertEqual(links[0].text, "a")
        self.assertEqual(links[1].text, "b")
        self.assertEqual(links[2].text, "c")

    def test_no_links_returns_empty_list(self):
        factory = LinkFactory(filepath=Path("/tmp/guide/SKILL.md"))
        links = factory.create_links("# No links here.")

        self.assertEqual(links, [])


class TestLinkMapper(unittest.TestCase):
    def test_single_matching_rule(self):
        mapper = LinkMapper()
        link = Link(
            raw="[text](./file.md)",
            kind="markdown",
            text="text",
            path="./file.md",
            fragment="",
            is_image=False,
            context=LinkLocation(
                filepath=Path("/tmp/guide/SKILL.md"),
                skill=None,
                start=0,
                end=18,
            ),
        )
        context = LinkContext(
            skill=None,
            filepath=Path("/tmp/guide/SKILL.md"),
            file_skill=None,
            repo_root=Path("/tmp"),
            skills={},
            source_to_target={},
            target_to_source={},
            all_source_files=set(),
            target_to_skill={},
            source_to_skill={},
        )
        with self.assertRaises(RuntimeError):
            # Matching rule exists but target is not resolved
            mapper.map(link, context)

    def test_no_matching_rule_raises(self):
        mapper = LinkMapper()
        link = Link(
            raw="[[plain]]",
            kind="wiki",
            text="plain",
            path="plain",
            fragment="",
            is_image=False,
            context=LinkLocation(
                filepath=Path("/tmp/guide/SKILL.md"),
                skill=None,
                start=0,
                end=9,
            ),
        )
        context = LinkContext(
            skill=None,
            filepath=Path("/tmp/guide/SKILL.md"),
            file_skill=None,
            repo_root=Path("/tmp"),
            skills={},
            source_to_target={},
            target_to_source={},
            all_source_files=set(),
            target_to_skill={},
            source_to_skill={},
        )
        with self.assertRaises(LinkMapError) as cm:
            mapper.map(link, context)
        self.assertIn("no matching rule", str(cm.exception))

    def test_multiple_matching_rules_raises(self):
        class FakeRule:
            def match(self, link):
                return True
            def apply(self, link, context):
                return ""
        mapper = LinkMapper(rules=[FakeRule(), FakeRule()])
        link = Link(
            raw="[text](./file.md)",
            kind="markdown",
            text="text",
            path="./file.md",
            fragment="",
            is_image=False,
            context=LinkLocation(
                filepath=Path("/tmp/guide/SKILL.md"),
                skill=None,
                start=0,
                end=18,
            ),
        )
        context = LinkContext(
            skill=None,
            filepath=Path("/tmp/guide/SKILL.md"),
            file_skill=None,
            repo_root=Path("/tmp"),
            skills={},
            source_to_target={},
            target_to_source={},
            all_source_files=set(),
            target_to_skill={},
            source_to_skill={},
        )
        with self.assertRaises(LinkMapError) as cm:
            mapper.map(link, context)
        self.assertIn("ambiguous", str(cm.exception))


class TestLinkReplacer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_creates_copy_and_returns_path(self):
        md = self.tmpdir / "guide.md"
        md.write_text("# Guide\nSee [other](./other.md).")

        replacer = LinkReplacer()
        context = LinkContext(
            skill=None,
            filepath=md,
            file_skill=None,
            repo_root=self.tmpdir,
            skills={},
            source_to_target={},
            target_to_source={},
            all_source_files=set(),
            target_to_skill={},
            source_to_skill={},
        )
        result = replacer.replace(context)

        self.assertTrue(result.new_path.exists())
        self.assertNotEqual(result.new_path, md)
        self.assertIn("./other.md", result.new_path.read_text())
        self.assertEqual(len(result.fixes), 1)
        self.assertEqual(result.fixes[0]["status"], "broken")

    def test_skips_external_links(self):
        md = self.tmpdir / "guide.md"
        md.write_text("# Guide\nSee [example](https://example.com).")

        replacer = LinkReplacer()
        context = LinkContext(
            skill=None,
            filepath=md,
            file_skill=None,
            repo_root=self.tmpdir,
            skills={},
            source_to_target={},
            target_to_source={},
            all_source_files=set(),
            target_to_skill={},
            source_to_skill={},
        )
        result = replacer.replace(context)

        self.assertIn("https://example.com", result.new_path.read_text())
        self.assertEqual(len(result.fixes), 0)

    def test_replace_skill_local_source(self):
        """replace_skill processes all markdown files of a local skill."""
        source = LocalSource(path=self.tmpdir)

        guide_dir = self.tmpdir / "guide"
        guide_dir.mkdir()
        guide_md = guide_dir / "SKILL.md"
        guide_md.write_text("---\nname: guide\n---\n# Guide\nSee [other](../other/SKILL.md).")
        guide_skill = Skill(file_path=guide_md, folder_path=guide_dir, source=source)

        other_dir = self.tmpdir / "other"
        other_dir.mkdir()
        other_md = other_dir / "SKILL.md"
        other_md.write_text("---\nname: other\n---\n# Other")

        replacer = LinkReplacer()
        results = replacer.replace_skill(guide_skill)

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertTrue(result.new_path.exists())
        content = result.new_path.read_text()
        self.assertNotIn("../other/SKILL.md", content)
        self.assertIn("[other](skill: other)", content)
        self.assertEqual(len(result.fixes), 1)
        self.assertEqual(result.fixes[0]["status"], "fixed")

    def test_replace_skill_flat_local_source(self):
        """replace_skill works for flat skills."""
        source = LocalSource(path=self.tmpdir)

        guide_md = self.tmpdir / "guide.skill.md"
        guide_md.write_text("---\nname: guide\n---\n# Guide")
        guide_skill = Skill(file_path=guide_md, folder_path=None, source=source)

        replacer = LinkReplacer()
        results = replacer.replace_skill(guide_skill)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].fixes, [])


if __name__ == "__main__":
    unittest.main()
