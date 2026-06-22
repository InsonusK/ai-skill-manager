"""Tests for AdapterMessage."""

import unittest

from ai_skill_manager.adapters.models.adapter_message import AdapterMessage


class TestAdapterMessage(unittest.TestCase):
    def test_str_formats_message(self):
        msg = AdapterMessage("count: {count}", {"count": 5})
        self.assertEqual(str(msg), "count: 5")

    def test_repr_contains_message_and_params(self):
        msg = AdapterMessage("count: {count}", {"count": 5})
        self.assertIn("count: {count}", repr(msg))
        self.assertIn("5", repr(msg))

    def test_to_log_equals_str(self):
        msg = AdapterMessage("done", {})
        self.assertEqual(msg.to_log(), "done")


if __name__ == "__main__":
    unittest.main()
