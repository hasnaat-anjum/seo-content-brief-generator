"""Tests for draft scoring and readability."""

import os
import unittest

from seo_brief.brief import build_brief
from seo_brief.score import flesch_reading_ease, score_draft
from tests import load_example_pages

SEED = "best budget espresso machine for beginners"


def _perfect_draft(brief):
    """Build a draft that follows the brief closely, ~600 words."""
    filler = ("Fresh beans and clean water make every shot taste better. "
              "A clean machine lasts longer and makes better coffee. ")
    lines = ["# %s" % brief.titles[0], ""]
    lines.append("This guide to %s covers everything a beginner needs. "
                 "It explains the pump, the grinder, the milk wand, the "
                 "basket, the beans, the steam and the shot."
                 % SEED)
    for section in brief.outline:
        lines.append("## %s" % section["title"])
        lines.append("This section explains %s in plain words. "
                     "The built-in grinder, the milk, the coffee, the wand, "
                     "the bar, the pump, the beans, the steam, the basket "
                     "and the shot all matter here." % section["title"].lower())
        lines.append(filler * 2)
        for sub in section.get("subheadings", [])[:2]:
            lines.append("### %s" % sub)
            lines.append(filler)
    draft = "\n\n".join(lines)
    # Pad to the target length with simple sentences.
    while len(draft.split()) < brief.target_words * 0.95:
        draft += "\n\n" + filler * 4
    return draft


class TestFlesch(unittest.TestCase):
    def test_simple_text_scores_high(self):
        score, _ = flesch_reading_ease(
            "The cat sat on the mat. The dog ran in the park. "
            "We had tea and cake.")
        self.assertGreaterEqual(score, 80)

    def test_dense_text_scores_low(self):
        score, _ = flesch_reading_ease(
            "The quintessential characteristics of epistemological "
            "methodologies necessitate comprehensive substantiation "
            "through multifaceted analytical frameworks.")
        self.assertLess(score, 40)

    def test_empty_text_is_zero(self):
        score, _ = flesch_reading_ease("")
        self.assertEqual(score, 0.0)


class TestScoreDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brief = build_brief(SEED, load_example_pages())
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "examples", "sample-draft.md"),
                  encoding="utf-8") as handle:
            cls.sample_draft = handle.read()

    def test_sample_draft_scores_76_grade_c(self):
        result = score_draft(self.sample_draft, self.brief)
        self.assertEqual(result["score"], 76)
        self.assertEqual(result["grade"], "C")
        self.assertEqual(result["word_count"], 314)
        self.assertEqual(len(result["fixes"]), 3)

    def test_perfect_draft_scores_high(self):
        draft = _perfect_draft(self.brief)
        result = score_draft(draft, self.brief)
        self.assertGreaterEqual(result["score"], 90)
        self.assertEqual(result["grade"], "A")

    def test_empty_draft_scores_zero(self):
        result = score_draft("", self.brief)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["grade"], "F")

    def test_keyword_missing_from_title_loses_points(self):
        draft = "# A Guide to Coffee\n\n" + "Coffee is great. " * 100
        result = score_draft(draft, self.brief)
        title_check = next(c for c in result["checks"]
                           if c["name"].startswith("Keyword in the title"))
        self.assertEqual(title_check["points"], 0)

    def test_checks_add_up_to_score(self):
        result = score_draft(self.sample_draft, self.brief)
        total = sum(c["points"] for c in result["checks"])
        self.assertEqual(total, result["score"])

    def test_grade_boundaries(self):
        # A draft scoring 100 by construction is grade A; empty is F.
        self.assertEqual(score_draft(_perfect_draft(self.brief),
                                     self.brief)["grade"], "A")


if __name__ == "__main__":
    unittest.main()
