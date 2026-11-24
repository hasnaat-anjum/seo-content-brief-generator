"""Tests for the must-include term extractor."""

import unittest

from seo_brief.terms import load_niches, term_coverage, tokenize, top_terms
from tests import load_example_pages


class TestTokenize(unittest.TestCase):
    def test_stopwords_removed(self):
        tokens = tokenize("The quick brown fox jumps over the lazy dog")
        self.assertNotIn("the", tokens)
        self.assertIn("quick", tokens)
        self.assertIn("fox", tokens)

    def test_lowercased(self):
        self.assertEqual(tokenize("Espresso MACHINE"), ["espresso", "machine"])


class TestTopTerms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = load_example_pages()
        cls.seed = "best budget espresso machine for beginners"
        cls.terms = top_terms(cls.pages, cls.seed)

    def test_returns_ranked_terms(self):
        self.assertEqual(len(self.terms), 15)
        top = self.terms[0]
        self.assertEqual(top["term"], "grinder")
        self.assertEqual(top["pages"], 3)

    def test_seed_words_excluded(self):
        found = {t["term"] for t in self.terms}
        self.assertNotIn("espresso", found)
        self.assertNotIn("machine", found)
        # Plurals of seed words are excluded too.
        self.assertNotIn("machines", found)

    def test_generic_words_excluded(self):
        found = {t["term"] for t in self.terms}
        self.assertNotIn("good", found)
        self.assertNotIn("make", found)
        self.assertNotIn("better", found)

    def test_bigrams_included(self):
        found = {t["term"] for t in self.terms}
        self.assertIn("built-in grinder", found)
        self.assertIn("steam wand", found)

    def test_scores_are_sorted(self):
        scores = [t["score"] for t in self.terms]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_empty_pages_give_no_terms(self):
        self.assertEqual(top_terms([], self.seed), [])


class TestTermCoverage(unittest.TestCase):
    def test_found_and_missing(self):
        found, missing = term_coverage(
            "The grinder and the milk frother work well.",
            ["grinder", "milk", "pump"])
        self.assertEqual(found, ["grinder", "milk"])
        self.assertEqual(missing, ["pump"])

    def test_whole_words_only(self):
        # "bar" must not match "barista".
        found, missing = term_coverage(
            "The barista made a great coffee.", ["bar"])
        self.assertEqual(found, [])
        self.assertEqual(missing, ["bar"])

    def test_multiword_terms(self):
        found, _ = term_coverage("Use a built-in grinder for best results.",
                                 ["built-in grinder"])
        self.assertEqual(found, ["built-in grinder"])


class TestNiches(unittest.TestCase):
    def test_niches_load(self):
        niches = load_niches()
        self.assertGreaterEqual(len(niches), 6)
        names = [n["name"] for n in niches]
        self.assertIn("Ecommerce / online shop", names)
        for niche in niches:
            self.assertGreaterEqual(len(niche["seeds"]), 1)


if __name__ == "__main__":
    unittest.main()
