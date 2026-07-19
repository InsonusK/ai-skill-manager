"""Tests for sync result formatter."""

import unittest
from pathlib import Path

from ai_skill_manager.cli.common.formatters import build_sync_errors_tree, format_sync_result
from ai_skill_manager.models.link_validation_error import LinkValidationError
from ai_skill_manager.sync_exception import SyncFailedError


class TestSyncFormatter(unittest.TestCase):
    def test_basic_sync(self):
        result = {"skills_count": 3}
        output = format_sync_result(result)
        self.assertIn("Synced: 3 skills", output)

    def test_dry_run(self):
        result = {"skills_count": 1, "dry_run": True}
        output = format_sync_result(result)
        self.assertIn("Dry run - no changes", output)


def _link_error(
    skill_name="skill-a",
    skill_path="skill-a",
    file_relative_path="SKILL.md",
    link_raw="[b](../b.md)",
    message="does not exist",
) -> LinkValidationError:
    return LinkValidationError(
        skill_name=skill_name,
        skill_path=Path(skill_path),
        file_relative_path=Path(file_relative_path),
        link_raw=link_raw,
        message=message,
    )


class TestBuildSyncErrorsTree(unittest.TestCase):
    """Pins the exact node shape/nesting fed into rich.tree.Tree, so a future
    edit that reshuffles the formatting can't silently break it without a
    failing test."""

    def test_root_label_reports_total_error_count(self):
        error = SyncFailedError(
            ["Duplicate skill name 'x'", _link_error(), _link_error(link_raw="[c](../c.md)")],
            target_dir=Path("/target"),
        )
        tree = build_sync_errors_tree(error)
        self.assertIn("3 error(s)", str(tree.label))

    def test_plain_string_error_is_a_flat_leaf(self):
        error = SyncFailedError(["Duplicate skill name 'x': found at both a and b"], target_dir=Path("/target"))
        tree = build_sync_errors_tree(error)

        self.assertEqual(len(tree.children), 1)
        self.assertEqual(str(tree.children[0].label), "Duplicate skill name 'x': found at both a and b")

    def test_link_error_nests_as_skill_file_link(self):
        error = SyncFailedError(
            [_link_error(
                skill_name="skill-a",
                skill_path="skill-a",
                file_relative_path="SKILL.md",
                link_raw="[b](../b.md)",
                message="target does not exist",
            )],
            target_dir=Path("/target"),
        )
        tree = build_sync_errors_tree(error)

        self.assertEqual(len(tree.children), 1)
        skill_node = tree.children[0]
        self.assertEqual(skill_node.label.plain, "Skill skill-a\npath: skill-a")

        self.assertEqual(len(skill_node.children), 1)
        file_node = skill_node.children[0]
        self.assertEqual(file_node.label.plain, "File SKILL.md")

        self.assertEqual(len(file_node.children), 1)
        link_node = file_node.children[0]
        self.assertEqual(link_node.label.plain, "Link [b](../b.md)\nerror: target does not exist")

    def test_multiple_links_in_same_file_share_one_skill_and_file_node(self):
        error = SyncFailedError(
            [
                _link_error(link_raw="[b](../b.md)", message="first error"),
                _link_error(link_raw="[c](../c.md)", message="second error"),
            ],
            target_dir=Path("/target"),
        )
        tree = build_sync_errors_tree(error)

        self.assertEqual(len(tree.children), 1)
        file_node = tree.children[0].children[0]
        self.assertEqual(len(file_node.children), 2)
        self.assertEqual(file_node.children[0].label.plain, "Link [b](../b.md)\nerror: first error")
        self.assertEqual(file_node.children[1].label.plain, "Link [c](../c.md)\nerror: second error")

    def test_multiple_files_in_same_skill_share_one_skill_node(self):
        error = SyncFailedError(
            [
                _link_error(file_relative_path="SKILL.md"),
                _link_error(file_relative_path="notes.md"),
            ],
            target_dir=Path("/target"),
        )
        tree = build_sync_errors_tree(error)

        self.assertEqual(len(tree.children), 1)
        skill_node = tree.children[0]
        self.assertEqual(len(skill_node.children), 2)
        self.assertEqual(skill_node.children[0].label.plain, "File SKILL.md")
        self.assertEqual(skill_node.children[1].label.plain, "File notes.md")

    def test_different_skills_each_get_their_own_node(self):
        error = SyncFailedError(
            [
                _link_error(skill_name="skill-a", skill_path="skill-a"),
                _link_error(skill_name="skill-b", skill_path="skill-b"),
            ],
            target_dir=Path("/target"),
        )
        tree = build_sync_errors_tree(error)

        self.assertEqual(len(tree.children), 2)
        self.assertEqual(tree.children[0].label.plain, "Skill skill-a\npath: skill-a")
        self.assertEqual(tree.children[1].label.plain, "Skill skill-b\npath: skill-b")

    def test_plain_errors_and_link_errors_can_be_mixed(self):
        error = SyncFailedError(
            ["Duplicate skill name 'x'", _link_error()],
            target_dir=Path("/target"),
        )
        tree = build_sync_errors_tree(error)

        self.assertEqual(len(tree.children), 2)
        self.assertEqual(str(tree.children[0].label), "Duplicate skill name 'x'")
        self.assertEqual(tree.children[1].label.plain, "Skill skill-a\npath: skill-a")


if __name__ == "__main__":
    unittest.main()
