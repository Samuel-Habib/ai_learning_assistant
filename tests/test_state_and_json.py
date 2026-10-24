import os
import unittest
import tempfile
import shutil

from assistant.json_utils import robust_json_loads, repair_json_string, extract_json_block
from assistant.db import StateManager

class TestRobustJson(unittest.TestCase):
    def test_clean_json(self):
        data = robust_json_loads('{"status": "ok", "count": 42}')
        self.assertEqual(data, {"status": "ok", "count": 42})

    def test_markdown_fence_and_preamble(self):
        text = "Here is the response:\n```json\n{\"modules\": [\"Algebra\", \"Calculus\"]}\n```\nEnjoy!"
        data = robust_json_loads(text)
        self.assertEqual(data, {"modules": ["Algebra", "Calculus"]})

    def test_trailing_commas(self):
        text = '{"items": [1, 2, 3, ], "meta": {"valid": True, }, }'
        data = robust_json_loads(text)
        self.assertEqual(data["items"], [1, 2, 3])
        self.assertTrue(data["meta"]["valid"])

    def test_unclosed_brackets(self):
        text = '{"list": [1, 2, 3'
        data = robust_json_loads(text)
        self.assertEqual(data, {"list": [1, 2, 3]})

    def test_fallback_default(self):
        self.assertEqual(robust_json_loads("Not json at all", default={"fallback": True}), {"fallback": True})

class TestStateManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.md_dir = os.path.join(self.test_dir, "md")
        self.sm = StateManager(db_path=self.db_path, md_dir=self.md_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_subject_crud(self):
        subj = self.sm.get_or_create_subject("calculus", "Calculus I")
        self.assertEqual(subj["name"], "calculus")
        self.assertEqual(subj["display_name"], "Calculus I")
        self.assertEqual(subj["frontier_level"], 1.0)

        self.sm.set_subject_boundary("calculus", 2.5, "Derivatives")
        updated = self.sm.get_subject("calculus")
        self.assertEqual(updated["frontier_level"], 2.5)
        self.assertEqual(updated["boundary_description"], "Derivatives")

    def test_curriculum_and_obsidian_sync(self):
        modules = [
            ("Limits", "Epsilon-delta"),
            ("Derivatives", "Power and chain rule"),
            ("Integrals", "Riemann sums")
        ]
        self.sm.save_curriculum_modules("calculus", modules, boundary_level=2.0)
        retrieved = self.sm.get_curriculum_modules("calculus")
        self.assertEqual(len(retrieved), 3)

        self.sm.sync_to_obsidian(active_subject="calculus")

        master_index = os.path.join(self.md_dir, "00_INDEX_DASHBOARD.md")
        self.assertTrue(os.path.exists(master_index))
        with open(master_index, "r") as f:
            content = f.read()
            self.assertIn("Calculus", content)
            self.assertIn("[[subjects/calculus/00_DASHBOARD|Calculus]]", content)

        subj_dashboard = os.path.join(self.md_dir, "subjects", "calculus", "00_DASHBOARD.md")
        self.assertTrue(os.path.exists(subj_dashboard))

        subj_roadmap = os.path.join(self.md_dir, "subjects", "calculus", "01_ROADMAP.md")
        self.assertTrue(os.path.exists(subj_roadmap))
        with open(subj_roadmap, "r") as f:
            r_content = f.read()
            self.assertIn("Limits", r_content)
            self.assertIn("Derivatives", r_content)

    def test_diagnostic_and_chat_history(self):
        self.sm.record_diagnostic_result(
            subject="calculus",
            level=1.5,
            topic="Limits",
            question="What is lim x->0 sin(x)/x?",
            response="1",
            passed=True,
            analysis="Correct application of limit"
        )
        history = self.sm.get_diagnostic_history("calculus")
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0]["passed"])

        self.sm.append_chat_message("calculus", "user", "How do I do substitution?")
        self.sm.append_chat_message("calculus", "assistant", "Choose u...")
        chats = self.sm.get_chat_history("calculus", limit=5)
        self.assertEqual(len(chats), 2)
        self.assertEqual(chats[0]["role"], "user")
        self.assertEqual(chats[1]["role"], "assistant")

class TestWordWrapAndCache(unittest.TestCase):
    def test_clean_word_wrap(self):
        from assistant.ui import wrap_text_cleanly
        text = "This is a detailed test to confirm that words like detail are never split across lines."
        wrapped = wrap_text_cleanly(text, max_width=30)
        for line in wrapped.split("\n"):
            # Ensure line does not exceed target width + small tolerance
            self.assertNotIn("detai\n", wrapped)
            self.assertIn("detail", wrapped)

    def test_llm_cache(self):
        from assistant.cache import LLMCache
        temp_dir = tempfile.mkdtemp()
        try:
            db_file = os.path.join(temp_dir, "cache_test.db")
            cache = LLMCache(db_path=db_file)
            self.assertIsNone(cache.get("test prompt", "gemini"))
            cache.set("test prompt", "cached answer", "gemini")
            self.assertEqual(cache.get("test prompt", "gemini"), "cached answer")
            stats = cache.get_stats()
            self.assertEqual(stats["total_entries"], 1)
            self.assertEqual(stats["total_hits"], 1)
        finally:
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    unittest.main()
