"""Integration tests for multi-target sync via the sync command API."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.command.sync import run_sync


class TestMultiTargetSync(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _make_source_dir(self):
        src = self.tmp / "skills"
        src.mkdir()
        (src / "guide.skill.md").write_text(
            "---\nname: guide\nwhenToUse: use for onboarding\ntags:\n  - workflow\n---\n"
            "# Guide\n"
        )
        return src

    def _write_config(self, target_settings):
        config = self.tmp / "ai-skills.yaml"
        data = {
            "sources": [{"path": "./skills", "type": "local"}],
            "settings": {"target": target_settings},
        }
        config.write_text(json.dumps(data))
        return config

    def test_two_targets_with_different_adapters(self):
        self._make_source_dir()
        config = self._write_config({
            "default": {"path": "./agents"},
            "claude": {"path": "./claude-target", "adapters": ["claude-property-adapter"]},
        })

        result = run_sync(config_path=config)

        self.assertEqual(result["skills_count"], 1)
        self.assertEqual(set(result["targets"]), {"default", "claude"})

        default_skill = (self.tmp / "agents" / "guide" / "SKILL.md").read_text()
        claude_skill = (self.tmp / "claude-target" / "guide" / "SKILL.md").read_text()

        # The default target keeps whenToUse/tags untouched (link-adapter fallback only).
        self.assertIn("whenToUse: use for onboarding", default_skill)
        self.assertIn("tags:", default_skill)
        self.assertNotIn("## Metadata", default_skill)

        # The claude target reshapes frontmatter via claude-property-adapter.
        self.assertIn("when_to_use: use for onboarding", claude_skill)
        self.assertNotIn("whenToUse", claude_skill)
        self.assertIn("## Metadata", claude_skill)
        self.assertIn("tags:", claude_skill)

    def test_flat_string_target_still_works(self):
        self._make_source_dir()
        config = self._write_config("./target")

        result = run_sync(config_path=config)

        self.assertEqual(result["skills_count"], 1)
        self.assertEqual(set(result["targets"]), {"default"})
        self.assertTrue((self.tmp / "target" / "guide" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
