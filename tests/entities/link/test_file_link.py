"""Tests for the FileLink entity."""

import unittest

from ai_skill_manager.discovery.link.builder.markdown import MarkdownLinkBuilder
from ai_skill_manager.entities.link.file_link import FileLink
from ai_skill_manager.entities.link.link_target import SkillLinkTarget


class TestFileLink(unittest.TestCase):
    def _target(self):
        return SkillLinkTarget(skill_name="skill-b", relative_path=None)

    def test_stores_all_fields(self):
        target = self._target()
        link = FileLink(
            raw="[text](../skill-b/SKILL.md)",
            text="text",
            format=MarkdownLinkBuilder,
            start=0,
            end=27,
            header=None,
            is_image=False,
            target=target,
        )
        self.assertEqual(link.raw, "[text](../skill-b/SKILL.md)")
        self.assertEqual(link.text, "text")
        self.assertEqual(link.format, MarkdownLinkBuilder)
        self.assertEqual(link.start, 0)
        self.assertEqual(link.end, 27)
        self.assertIsNone(link.header)
        self.assertFalse(link.is_image)
        self.assertIs(link.target, target)

    def test_defaults_header_none_and_is_image_false(self):
        link = FileLink(
            raw="[text](a.md)", text="text", format=MarkdownLinkBuilder,
            start=0, end=10, target=self._target(),
        )
        self.assertIsNone(link.header)
        self.assertFalse(link.is_image)

    def test_image_link(self):
        link = FileLink(
            raw="![alt](a.png)", text="alt", format=MarkdownLinkBuilder,
            start=0, end=10, is_image=True, target=self._target(),
        )
        self.assertTrue(link.is_image)

    def test_header_preserved(self):
        link = FileLink(
            raw="[text](a.md#section)", text="text", format=MarkdownLinkBuilder,
            start=0, end=10, header="#section", target=self._target(),
        )
        self.assertEqual(link.header, "#section")


if __name__ == "__main__":
    unittest.main()
