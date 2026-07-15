"""Tests for the FileLink entity."""

import unittest

from ai_skill_manager.entities.link.file_link import FileLink
from ai_skill_manager.entities.link.link_data import LinkData
from ai_skill_manager.entities.link.link_target import SkillLinkTarget


class TestFileLink(unittest.TestCase):
    def _target(self):
        return SkillLinkTarget(skill_name="skill-b", relative_path=None)

    def _data(self, **overrides):
        defaults = dict(
            raw="[text](../skill-b/SKILL.md)",
            text="text",
            format="markdown",
            start=0,
            end=27,
            raw_path="../skill-b/SKILL.md",
            header=None,
            is_image=False,
        )
        defaults.update(overrides)
        return LinkData(**defaults)

    def test_stores_all_fields(self):
        target = self._target()
        link = FileLink(data=self._data(), target=target)
        self.assertEqual(link.raw, "[text](../skill-b/SKILL.md)")
        self.assertEqual(link.text, "text")
        self.assertEqual(link.format, "markdown")
        self.assertEqual(link.start, 0)
        self.assertEqual(link.end, 27)
        self.assertEqual(link.raw_path, "../skill-b/SKILL.md")
        self.assertIsNone(link.header)
        self.assertFalse(link.is_image)
        self.assertIs(link.target, target)

    def test_image_link(self):
        link = FileLink(data=self._data(is_image=True), target=self._target())
        self.assertTrue(link.is_image)

    def test_header_preserved(self):
        link = FileLink(data=self._data(header="#section"), target=self._target())
        self.assertEqual(link.header, "#section")

    def test_link_type_property(self):
        link = FileLink(data=self._data(), target=self._target())
        self.assertIs(link.link_type, FileLink)


if __name__ == "__main__":
    unittest.main()
