"""Tests for the Markdown / JSON / HTML renderers."""

import json
import unittest

from seo_brief.brief import build_brief
from seo_brief.report import (brief_to_html, brief_to_json,
                              brief_to_markdown, score_to_markdown)
from seo_brief.score import score_draft
from tests import load_example_pages

SEED = "best budget espresso machine for beginners"


class TestBriefRenderers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brief = build_brief(SEED, load_example_pages())

    def test_markdown_contains_key_sections(self):
        text = brief_to_markdown(self.brief)
        for heading in ("## Suggested titles", "## Outline",
                        "## Must-include terms", "## Questions to answer",
                        "## Competitors analysed", "## E-E-A-T checklist",
                        "## Call to action"):
            self.assertIn(heading, text)
        self.assertIn(SEED, text)

    def test_json_round_trips(self):
        data = json.loads(brief_to_json(self.brief))
        self.assertEqual(data["keyword"], SEED)
        self.assertEqual(data["target_words"], 600)

    def test_html_is_self_contained(self):
        html = brief_to_html(self.brief)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn(SEED, html)
        self.assertIn("<style>", html)
        # No external requests: no scripts, no remote URLs.
        self.assertNotIn("<script", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)


class TestScoreRenderer(unittest.TestCase):
    def test_score_markdown(self):
        brief = build_brief(SEED, load_example_pages())
        result = score_draft("# Test\n\nSome words here. " * 20, brief)
        text = score_to_markdown(result, SEED)
        self.assertIn("Score:", text)
        self.assertIn("Grade", text)


if __name__ == "__main__":
    unittest.main()
