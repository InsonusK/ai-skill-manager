"""Tests for Adapter orchestration."""

import unittest

from ai_skill_manager.adapters import Adapter
from ai_skill_manager.adapters.models.adapter_message import AdapterMessage
from ai_skill_manager.adapters.rules.abs_adapter import absAdapter
from ai_skill_manager.adapters.rules.link_adapter import LinkAdapter


class DummyAdapter(absAdapter):
    @classmethod
    def name(cls) -> str:
        return "dummy"

    @classmethod
    def version(cls) -> str:
        return "2.0.0"

    def adapt(self, old_skill, new_skill):
        name = new_skill.name if new_skill else "none"
        return AdapterMessage("adapted {skill}", {"skill": name})


class TestAdapter(unittest.TestCase):
    def test_registered_adapters_name_version(self):
        adapter = Adapter(skills=[])
        names = adapter.registered_adapters_name_version
        self.assertIn(("LinkAdapter", "1.0.0"), names)

    def test_adapt_runs_registered_adapters(self):
        adapter = Adapter(skills=[], adapter_list=[DummyAdapter])
        results = adapter.adapt(None, None)
        self.assertIn("dummy", results)
        self.assertEqual(str(results["dummy"]), "adapted none")

    def test_duplicate_adapter_names_raise(self):
        with self.assertRaises(AssertionError):
            Adapter(skills=[], adapter_list=[DummyAdapter, DummyAdapter])


if __name__ == "__main__":
    unittest.main()
