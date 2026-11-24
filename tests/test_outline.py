"""Tests for the outline builder."""

import unittest

from seo_brief.outline import build_outline, word_count_target
from tests import load_example_pages


class TestWordCountTarget(unittest.TestCase):
    def test_median_and_range(self):
        pages = load_example_pages()
        low, median, high = word_count_target(pages)
        counts = sorted(p.word_count for p in pages)
        self.assertEqual((low, high), (counts[0], counts[-1]))
        self.assertEqual(median, counts[1])

    def test_no_pages_is_zero(self):
        self.assertEqual(word_count_target([]), (0, 0, 0))


class TestBuildOutline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = load_example_pages()
        cls.sections = build_outline(cls.pages, 600)

    def test_merges_near_duplicate_sections(self):
        # "What to look for", "How to choose" and "What actually
        # matters" are one section, covered by all 3 pages.
        titles = [s.title for s in self.sections]
        self.assertIn("What to look for in a budget espresso machine",
                      titles)
        # The near-duplicates were folded into that one section.
        self.assertNotIn("How to choose a cheap espresso machine", titles)
        self.assertNotIn(
            "Budget espresso machines: what actually matters", titles)
        choose = next(s for s in self.sections
                      if s.title.startswith("What to look for"))
        self.assertEqual(choose.coverage, 3)

    def test_listicle_items_grouped_as_subheadings(self):
        picks = next(s for s in self.sections
                     if "picks" in s.title.lower())
        self.assertIn("Breville Bambino", picks.subheadings)
        self.assertIn("De'Longhi Dedica", picks.subheadings)
        self.assertEqual(len(picks.subheadings), 9)

    def test_faq_heading_dropped(self):
        titles = [s.title for s in self.sections]
        self.assertFalse(any("faq" in t.lower() for t in titles))

    def test_word_shares_add_up_to_target(self):
        total = sum(s.words for s in self.sections)
        self.assertEqual(total, 600)

    def test_most_covered_sections_first(self):
        coverages = [s.coverage for s in self.sections]
        self.assertEqual(coverages, sorted(coverages, reverse=True))

    def test_section_count_is_sane(self):
        self.assertEqual(len(self.sections), 7)

    def test_subheading_duplicate_not_a_section(self):
        # "How much should you spend?" is an H3 on one page and an H2
        # on another — it appears once, as a subheading.
        titles = [s.title for s in self.sections]
        self.assertNotIn("How much should you spend on your first "
                         "espresso machine?", titles)


if __name__ == "__main__":
    unittest.main()
