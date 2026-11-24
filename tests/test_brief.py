"""Tests for brief assembly."""

import unittest

from seo_brief.brief import (build_brief, meta_options, title_options)
from tests import load_example_pages

SEED = "best budget espresso machine for beginners"


class TestTitleOptions(unittest.TestCase):
    def test_five_options_within_60_chars(self):
        titles = title_options(SEED)
        self.assertEqual(len(titles), 5)
        for title in titles:
            self.assertLessEqual(len(title), 60)

    def test_no_doubled_best_or_beginners(self):
        for title in title_options(SEED):
            self.assertNotIn("Best Best", title)
            self.assertNotIn("Beginners for Beginners", title)

    def test_short_seed_also_five(self):
        titles = title_options("espresso machine")
        self.assertEqual(len(titles), 5)
        for title in titles:
            self.assertLessEqual(len(title), 60)

    def test_verb_seed_titles(self):
        titles = title_options("how to start a food blog")
        self.assertEqual(len(titles), 5)
        for title in titles:
            self.assertLessEqual(len(title), 60)
            self.assertNotIn("Best Start", title)


class TestMetaOptions(unittest.TestCase):
    def test_three_options_within_160_chars(self):
        metas = meta_options(SEED)
        self.assertEqual(len(metas), 3)
        for meta in metas:
            self.assertLessEqual(len(meta), 160)


class TestBuildBrief(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = load_example_pages()
        cls.brief = build_brief(SEED, cls.pages)

    def test_intent_and_content_type(self):
        self.assertEqual(self.brief.intent, "commercial")
        self.assertEqual(self.brief.content_type, "listicle")

    def test_target_words_from_competitor_median(self):
        # Competitor word counts 582-681, median 597 -> rounded to 600.
        self.assertEqual(self.brief.target_words, 600)
        self.assertEqual(self.brief.word_range["median"], 597)

    def test_outline_words_add_up(self):
        total = sum(s["words"] for s in self.brief.outline)
        self.assertEqual(total, self.brief.target_words)

    def test_titles_and_metas(self):
        self.assertEqual(len(self.brief.titles), 5)
        self.assertEqual(len(self.brief.meta_descriptions), 3)

    def test_questions_present(self):
        self.assertEqual(len(self.brief.questions), 10)
        self.assertIn("What is the best budget espresso machine "
                      "for beginners?", self.brief.questions)

    def test_competitor_table(self):
        self.assertEqual(len(self.brief.competitor_table), 3)
        scores = [row["score"] for row in self.brief.competitor_table]
        self.assertEqual(scores, [26, 24, 24])

    def test_gaps_capped(self):
        self.assertLessEqual(len(self.brief.gaps), 5)
        self.assertTrue(self.brief.gaps)

    def test_eeat_and_cta(self):
        self.assertGreaterEqual(len(self.brief.eeat_checklist), 5)
        self.assertIn("comparison table", self.brief.call_to_action)

    def test_id_is_slug_plus_date(self):
        self.assertTrue(
            self.brief.id.startswith("best-budget-espresso-machine-"
                                     "for-beginners-"))

    def test_round_trip_through_dict(self):
        from seo_brief.brief import Brief
        rebuilt = Brief.from_dict(self.brief.to_dict())
        self.assertEqual(rebuilt.keyword, self.brief.keyword)
        self.assertEqual(rebuilt.target_words, self.brief.target_words)
        self.assertEqual(rebuilt.outline, self.brief.outline)


class TestBuildBriefEdgeCases(unittest.TestCase):
    def test_keyword_only_brief_says_so(self):
        brief = build_brief("espresso machine", [])
        self.assertTrue(any("No competitor pages" in note
                            for note in brief.notes))
        self.assertEqual(brief.target_words, 800)
        self.assertEqual(brief.outline, [])
        # Generated questions still work without competitors.
        self.assertEqual(len(brief.questions), 10)

    def test_failed_fetch_reported_in_notes(self):
        from seo_brief.parse import Page
        pages = [Page(url="https://example.com/dead",
                      fetch_error="HTTP 404")]
        brief = build_brief("espresso machine", pages)
        self.assertTrue(any("could not be fetched" in note
                            for note in brief.notes))

    def test_intent_override(self):
        pages = load_example_pages()
        brief = build_brief(SEED, pages, intent_override="transactional")
        self.assertEqual(brief.intent, "transactional")

    def test_internal_link_suggestions(self):
        pages = load_example_pages()
        own = [
            {"title": "Espresso Machine Maintenance Guide",
             "url": "https://mysite.com/espresso-maintenance"},
            {"title": "Best Coffee Beans for Beginners",
             "url": "https://mysite.com/coffee-beans"},
            {"title": "How to Train a Puppy",
             "url": "https://mysite.com/puppy"},
        ]
        brief = build_brief(SEED, pages, own_pages=own)
        titles = [link["title"] for link in brief.internal_links]
        self.assertIn("Espresso Machine Maintenance Guide", titles)
        self.assertNotIn("How to Train a Puppy", titles)


if __name__ == "__main__":
    unittest.main()
