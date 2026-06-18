"""Tests for LinkUpdater adapter."""

import unittest
import tempfile
import shutil
from pathlib import Path

from ai_skill_manager.adapters.link_updater import LinkUpdater
from ai_skill_manager.commands.discover.core.base import SkillMapping


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

        updater = LinkUpdater([], {}, set())
        updater.adapt(md)

        content = md.read_text()
        self.assertEqual(content, "# Guide\nNo links here.")
        self.assertEqual(len(updater.fixes), 0)

    def test_external_link_unchanged(self):
        md = self.target / "guide.md"
        md.write_text("# Guide\nSee [example](https://example.com).")

        updater = LinkUpdater([], {}, set())
        updater.adapt(md)

        content = md.read_text()
        self.assertIn("https://example.com", content)
        self.assertEqual(len(updater.fixes), 0)

    def test_anchor_link_unchanged(self):
        md = self.target / "guide.md"
        md.write_text("# Guide\nSee [section](#section).")

        updater = LinkUpdater([], {}, set())
        updater.adapt(md)

        content = md.read_text()
        self.assertIn("#section", content)
        self.assertEqual(len(updater.fixes), 0)

    def test_absolute_link_unchanged(self):
        md = self.target / "guide.md"
        md.write_text("# Guide\nSee [root](/etc/passwd).")

        updater = LinkUpdater([], {}, set())
        updater.adapt(md)

        content = md.read_text()
        self.assertIn("/etc/passwd", content)
        self.assertEqual(len(updater.fixes), 0)

    def test_fix_managed_link_cross_skill(self):
        """Link to a file in another skill becomes a skill link."""
        # Setup source structure
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [other](./other.md).")
        source_other = source_dir / "other.md"
        source_other.write_text("# Other")

        # Setup target structure (simulating copied files)
        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [other](./other.md).")

        target_other = self.target / "other" / "SKILL.md"
        target_other.parent.mkdir()
        target_other.write_text("# Other")

        # Create mappings
        guide_mapping = SkillMapping(source_guide, target_guide.parent, "guide", True)
        other_mapping = SkillMapping(source_other, target_other.parent, "other", True)

        # Build source_to_target map
        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }

        updater = LinkUpdater([guide_mapping, other_mapping], source_to_target, {source_guide, source_other})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("./other.md", content)
        # Should be converted to skill link format
        self.assertIn("[other](other|uid:", content)

        # Check fix recorded
        fixes = [f for f in updater.fixes if f["status"] == "fixed"]
        self.assertEqual(len(fixes), 1)
        self.assertEqual(fixes[0]["old"], "[other](./other.md)")

    def test_dry_run_no_changes(self):
        """Dry run should not modify files but record fixes."""
        # Setup source
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [other](./other.md).")
        source_other = source_dir / "other.md"
        source_other.write_text("# Other")

        # Setup target
        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [other](./other.md).")

        target_other = self.target / "other" / "SKILL.md"
        target_other.parent.mkdir()
        target_other.write_text("# Other")

        guide_mapping = SkillMapping(source_guide, target_guide.parent, "guide", True)
        other_mapping = SkillMapping(source_other, target_other.parent, "other", True)

        source_to_target = {source_guide: target_guide, source_other: target_other}

        updater = LinkUpdater(
            [guide_mapping, other_mapping],
            source_to_target,
            {source_guide, source_other},
            dry_run=True
        )
        updater.adapt(target_guide)

        # File should be unchanged
        content = target_guide.read_text()
        self.assertIn("./other.md", content)

        # But fix should be recorded
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

        guide_mapping = SkillMapping(source_guide, target_guide.parent, "guide", True)

        updater = LinkUpdater([guide_mapping], {}, {source_guide})
        updater.adapt(target_guide)

        # Link stays as-is
        content = target_guide.read_text()
        self.assertIn("./missing.md", content)

        # But recorded as broken
        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)

    def test_external_existing_file(self):
        """Link to existing file outside sources is external."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [ext](./external.md).")

        # External file exists in source dir but not in our map
        external = source_dir / "external.md"
        external.write_text("# External")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [ext](./external.md).")

        guide_mapping = SkillMapping(source_guide, target_guide.parent, "guide", True)

        updater = LinkUpdater([guide_mapping], {}, {source_guide})
        updater.adapt(target_guide)

        # Should be recorded as external (file exists but not in source_to_target)
        ext = [f for f in updater.fixes if f["status"] == "external"]
        self.assertEqual(len(ext), 1)

    def test_adapt_all_recursive(self):
        """adapt_all processes all .md files recursively."""
        sub = self.target / "sub"
        sub.mkdir()

        md1 = self.target / "a.md"
        md1.write_text("# A")

        md2 = sub / "b.md"
        md2.write_text("# B")

        updater = LinkUpdater([], {}, set())
        updater.adapt_all(self.target)

        # Should process both files
        self.assertEqual(len(updater.fixes), 0)  # No links to fix

    def test_image_link(self):
        """Image links should also be processed."""
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

        guide_mapping = SkillMapping(source_guide, target_guide.parent, "guide", True)

        source_to_target = {source_guide: target_guide, source_img: target_img}

        updater = LinkUpdater([guide_mapping], source_to_target, {source_guide, source_img})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        # Check that the old relative link is gone and new one is present
        # Use regex-like check to ensure it's a proper link, not substring
        self.assertNotIn("](./img.png)", content)
        self.assertIn("](../img.png)", content)
        # Ensure image marker is preserved
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

        guide_mapping = SkillMapping(source_guide, target_guide.parent, "guide", True)
        other_mapping = SkillMapping(source_other, target_other.parent, "other", True)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }

        updater = LinkUpdater([guide_mapping, other_mapping], source_to_target, {source_guide, source_other})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("./other.md#section", content)
        # Should be skill link with fragment
        self.assertIn("[other](other|uid:", content)
        self.assertIn("|#section)", content)

        fixes = [f for f in updater.fixes if f["status"] == "fixed"]
        self.assertEqual(len(fixes), 1)
        self.assertEqual(fixes[0]["old"], "[other](./other.md#section)")

    def test_external_link_with_fragment(self):
        """External links with fragments should preserve the fragment and be marked external."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [ext](./external.md#section).")

        external = source_dir / "external.md"
        external.write_text("# External")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [ext](./external.md#section).")

        guide_mapping = SkillMapping(source_guide, target_guide.parent, "guide", True)

        updater = LinkUpdater([guide_mapping], {}, {source_guide})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        # External links point back to source; fragment is preserved
        self.assertIn("../../source/external.md#section", content)

        ext = [f for f in updater.fixes if f["status"] == "external"]
        self.assertEqual(len(ext), 1)
        self.assertEqual(ext[0]["new"], "[ext](../../source/external.md#section)")

    def test_broken_link_with_fragment(self):
        """Broken links with fragments should still be reported as broken."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()
        source_guide = source_dir / "guide.md"
        source_guide.write_text("# Guide\nSee [missing](./missing.md#section).")

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir()
        target_guide.write_text("# Guide\nSee [missing](./missing.md#section).")

        guide_mapping = SkillMapping(source_guide, target_guide.parent, "guide", True)

        updater = LinkUpdater([guide_mapping], {}, {source_guide})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("./missing.md#section", content)

        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)
        self.assertEqual(broken[0]["reason"], "target file does not exist")

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

        guide_mapping = SkillMapping(source_guide, target_guide.parent, "guide", True)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }

        updater = LinkUpdater([guide_mapping], source_to_target, {source_guide, source_other})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        # Same skill - relative path updated but not skill link
        self.assertNotIn("./other.md", content)
        self.assertIn("[other](other.md)", content)

    def test_wiki_link_by_name_same_skill(self):
        """Wiki link by name within same skill becomes relative markdown."""
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

        guide_mapping = SkillMapping(source_dir, target_guide.parent, "guide", False)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater([guide_mapping], source_to_target, all_source_files)
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("[[other]]", content)
        self.assertIn("[other](other.md)", content)

    def test_wiki_link_by_name_cross_skill(self):
        """Wiki link by name to another skill becomes skill link."""
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

        guide_mapping = SkillMapping(source_guide.parent, target_guide.parent, "guide", False)
        other_mapping = SkillMapping(source_other.parent, target_other.parent, "other", False)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater([guide_mapping, other_mapping], source_to_target, all_source_files)
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("[[other]]", content)
        self.assertIn("[other](other|uid:", content)

    def test_wiki_link_with_header_and_custom_text(self):
        """Wiki link with header and custom text produces correct skill link."""
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

        guide_mapping = SkillMapping(source_guide.parent, target_guide.parent, "guide", False)
        other_mapping = SkillMapping(source_other.parent, target_other.parent, "other", False)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater([guide_mapping, other_mapping], source_to_target, all_source_files)
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("[[other#section|Custom Name]]", content)
        self.assertIn("[Custom Name](other|uid:", content)
        self.assertIn("|#section)", content)

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

        guide_mapping = SkillMapping(source_guide.parent, target_guide.parent, "guide", False)
        other_mapping = SkillMapping(source_other.parent, target_other.parent, "other", False)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater([guide_mapping, other_mapping], source_to_target, all_source_files)
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("[[../other/SKILL.md]]", content)
        self.assertIn("[SKILL.md](other|uid:", content)

    def test_wiki_link_by_absolute_path(self):
        """Wiki link with absolute path resolves correctly."""
        source_dir = self.tmpdir / "source"
        source_dir.mkdir()

        source_other = source_dir / "other" / "SKILL.md"
        source_other.parent.mkdir(parents=True)
        source_other.write_text("# Other")

        source_guide = source_dir / "guide" / "SKILL.md"
        source_guide.parent.mkdir(parents=True)
        source_guide.write_text("# Guide\nSee [[{}]].".format(source_other))

        target_guide = self.target / "guide" / "SKILL.md"
        target_guide.parent.mkdir(parents=True)
        target_guide.write_text("# Guide\nSee [[{}]].".format(source_other))

        target_other = self.target / "other" / "SKILL.md"
        target_other.parent.mkdir(parents=True)
        target_other.write_text("# Other")

        guide_mapping = SkillMapping(source_guide.parent, target_guide.parent, "guide", False)
        other_mapping = SkillMapping(source_other.parent, target_other.parent, "other", False)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater([guide_mapping, other_mapping], source_to_target, all_source_files)
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("[[{}]]".format(source_other), content)
        self.assertIn("[SKILL.md](other|uid:", content)

    def test_wiki_link_ambiguous_name(self):
        """Wiki link by name matching multiple files is left unchanged and warned."""
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

        guide_mapping = SkillMapping(source_guide.parent, target_guide.parent, "guide", False)

        source_to_target = {source_guide: target_guide}
        all_source_files = {source_guide, source_common1, source_common2}

        updater = LinkUpdater([guide_mapping], source_to_target, all_source_files)
        updater.adapt(target_guide)

        content = target_guide.read_text()
        # Ambiguous link should remain unchanged
        self.assertIn("[[common.md]]", content)

        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)
        self.assertIn("target file does not exist", broken[0]["reason"])

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

        guide_mapping = SkillMapping(source_guide.parent, target_guide.parent, "guide", False)

        updater = LinkUpdater([guide_mapping], {}, {source_guide})
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertIn("[[missing]]", content)

        broken = [f for f in updater.fixes if f["status"] == "broken"]
        self.assertEqual(len(broken), 1)

    def test_wiki_link_same_skill_with_header(self):
        """Wiki link with header within same skill preserves header in relative link."""
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

        guide_mapping = SkillMapping(source_guide.parent, target_guide.parent, "guide", False)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater([guide_mapping], source_to_target, all_source_files)
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("[[other#section]]", content)
        self.assertIn("[other](other.md#section)", content)

    def test_wiki_link_by_name_with_custom_text_same_skill(self):
        """Wiki link with custom text within same skill uses custom text."""
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

        guide_mapping = SkillMapping(source_guide.parent, target_guide.parent, "guide", False)

        source_to_target = {
            source_guide: target_guide,
            source_other: target_other,
        }
        all_source_files = {source_guide, source_other}

        updater = LinkUpdater([guide_mapping], source_to_target, all_source_files)
        updater.adapt(target_guide)

        content = target_guide.read_text()
        self.assertNotIn("[[other|My Other File]]", content)
        self.assertIn("[My Other File](other.md)", content)


if __name__ == "__main__":
    unittest.main()
