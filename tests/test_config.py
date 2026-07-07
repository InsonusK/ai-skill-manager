"""Tests for config module."""

import unittest
import tempfile
import json
from pathlib import Path

from ai_skill_manager.adapters.rules import ClaudePropertyAdapter, LinkAdapter
from ai_skill_manager.config import load_config, parse_target_settings


class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_load_json(self):
        config_file = self.tmpdir / 'config.json'
        config_file.write_text(json.dumps({'key': 'value', 'num': 42}))

        result = load_config(config_file)
        self.assertEqual(result['key'], 'value')
        self.assertEqual(result['num'], 42)

    def test_load_yaml(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")

        config_file = self.tmpdir / 'config.yaml'
        config_file.write_text('key: value\nnum: 42\n')

        result = load_config(config_file)
        self.assertEqual(result['key'], 'value')
        self.assertEqual(result['num'], 42)

    def test_load_yml_extension(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")

        config_file = self.tmpdir / 'config.yml'
        config_file.write_text('test: true\n')

        result = load_config(config_file)
        self.assertTrue(result['test'])

    def test_load_invalid_json(self):
        config_file = self.tmpdir / 'bad.json'
        config_file.write_text('not json {')

        with self.assertRaises(json.JSONDecodeError):
            load_config(config_file)


class TestParseTargetSettings(unittest.TestCase):
    def test_flat_string_backward_compatible(self):
        specs = parse_target_settings(".agents/skills")

        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].name, "default")
        self.assertEqual(specs[0].path, Path(".agents/skills"))
        self.assertEqual(specs[0].adapters, [LinkAdapter])

    def test_none_defaults_like_flat_string(self):
        specs = parse_target_settings(None)

        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].name, "default")
        self.assertEqual(specs[0].path, Path(".agents/skills"))
        self.assertEqual(specs[0].adapters, [LinkAdapter])

    def test_multi_target_with_for_each_and_reserved_defaults(self):
        specs = parse_target_settings({
            "for_each": {"adapters": ["link-adapter"]},
            "default": {},
            "claude": {"adapters": ["claude-property-adapter"]},
        })

        by_name = {spec.name: spec for spec in specs}
        self.assertEqual(set(by_name), {"default", "claude"})

        self.assertEqual(by_name["default"].path, Path(".agents/skills"))
        self.assertEqual(by_name["default"].adapters, [LinkAdapter])

        self.assertEqual(by_name["claude"].path, Path(".claude/skills"))
        self.assertEqual(
            by_name["claude"].adapters, [LinkAdapter, ClaudePropertyAdapter]
        )

    def test_explicit_path_overrides_reserved_default(self):
        specs = parse_target_settings({"default": {"path": "./out"}})

        self.assertEqual(specs[0].path, Path("./out"))

    def test_custom_target_name_requires_path(self):
        with self.assertRaises(ValueError):
            parse_target_settings({"custom": {}})

    def test_unknown_adapter_name_raises(self):
        with self.assertRaises(ValueError):
            parse_target_settings({"default": {"adapters": ["nope"]}})

    def test_adapters_deduplicated_preserving_order(self):
        specs = parse_target_settings({
            "for_each": {"adapters": ["link-adapter"]},
            "default": {"adapters": ["link-adapter", "claude-property-adapter"]},
        })

        self.assertEqual(
            specs[0].adapters, [LinkAdapter, ClaudePropertyAdapter]
        )

    def test_invalid_target_type_raises(self):
        with self.assertRaises(ValueError):
            parse_target_settings(123)


if __name__ == '__main__':
    unittest.main()
