"""End-to-end CLI tests (in a temporary directory)."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date

from seo_brief.cli import main
from tests import example_files

SEED = "best budget espresso machine for beginners"


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = os.path.join(self.tmp.name, "briefs.json")
        self.brief_id = ("best-budget-espresso-machine-for-beginners-"
                         + date.today().strftime("%Y%m%d"))

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, argv):
        """Run main() with --store first; returns (exit_code, stdout)."""
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["--store", self.store] + argv)
        return code, out.getvalue()


class TestCliNew(CliTestCase):
    def test_new_from_files_saves_and_writes(self):
        out_path = os.path.join(self.tmp.name, "brief.md")
        code, stdout = self.run_cli([
            "new", SEED,
            "--file", example_files()[0],
            "--file", example_files()[1],
            "--file", example_files()[2],
            "--save", "--out", out_path,
        ])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("# Content Brief: %s" % SEED, text)
        self.assertIn("## Outline", text)
        # Saved to the store too.
        with open(self.store, encoding="utf-8") as handle:
            stored = json.load(handle)
        self.assertIn(self.brief_id, stored)

    def test_new_keyword_only_warns_but_succeeds(self):
        code, stdout = self.run_cli(["new", "espresso machine"])
        self.assertEqual(code, 0)
        self.assertIn("Content Brief: espresso machine", stdout)


class TestCliBriefCommands(CliTestCase):
    def setUp(self):
        super().setUp()
        self.run_cli(["new", SEED,
                      "--file", example_files()[0],
                      "--file", example_files()[1],
                      "--file", example_files()[2],
                      "--save"])

    def test_list_shows_saved_brief(self):
        code, stdout = self.run_cli(["list"])
        self.assertEqual(code, 0)
        self.assertIn(self.brief_id, stdout)
        self.assertIn(SEED, stdout)

    def test_show_prints_brief(self):
        code, stdout = self.run_cli(["show", self.brief_id])
        self.assertEqual(code, 0)
        self.assertIn("## Outline", stdout)

    def test_export_writes_json(self):
        out_path = os.path.join(self.tmp.name, "brief.json")
        code, _ = self.run_cli(["export", self.brief_id,
                                "--format", "json", "--out", out_path])
        self.assertEqual(code, 0)
        with open(out_path, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["keyword"], SEED)

    def test_score_sample_draft(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        draft = os.path.join(here, "examples", "sample-draft.md")
        code, stdout = self.run_cli(
            ["score", draft, "--brief-id", self.brief_id])
        self.assertEqual(code, 0)
        self.assertIn("76/100 (Grade C)", stdout)

    def test_score_without_brief_fails(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        draft = os.path.join(here, "examples", "sample-draft.md")
        code, _ = self.run_cli(["score", draft])
        self.assertEqual(code, 1)

    def test_delete_removes_brief(self):
        code, stdout = self.run_cli(["delete", self.brief_id])
        self.assertEqual(code, 0)
        code, stdout = self.run_cli(["list"])
        self.assertNotIn(self.brief_id, stdout)


class TestCliHelpers(CliTestCase):
    def test_questions(self):
        code, stdout = self.run_cli(["questions", SEED])
        self.assertEqual(code, 0)
        self.assertIn("How to choose a budget espresso machine?", stdout)

    def test_titles(self):
        code, stdout = self.run_cli(["titles", SEED])
        self.assertEqual(code, 0)
        self.assertIn("Best Budget Espresso Machine for Beginners", stdout)

    def test_niches(self):
        code, stdout = self.run_cli(["niches"])
        self.assertEqual(code, 0)
        self.assertIn("Ecommerce / online shop", stdout)

    def test_show_unknown_id_fails(self):
        code, _ = self.run_cli(["show", "does-not-exist"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
