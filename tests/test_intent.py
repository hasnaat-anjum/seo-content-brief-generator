"""Tests for search-intent classification and content-type picking."""

import unittest

from seo_brief.intent import classify_intent, content_type_for


class TestClassifyIntent(unittest.TestCase):
    def test_question_word_is_informational(self):
        result = classify_intent("how to fix a leaking tap")
        self.assertEqual(result["intent"], "informational")

    def test_best_is_commercial(self):
        result = classify_intent("best budget espresso machine")
        self.assertEqual(result["intent"], "commercial")
        self.assertIn("best", result["signal"])

    def test_vs_is_commercial(self):
        self.assertEqual(classify_intent("gaggia vs breville")["intent"],
                         "commercial")

    def test_buy_is_transactional(self):
        self.assertEqual(classify_intent("buy running shoes")["intent"],
                         "transactional")

    def test_cheap_is_transactional(self):
        self.assertEqual(classify_intent("cheap flights to london")["intent"],
                         "transactional")

    def test_price_is_transactional(self):
        self.assertEqual(classify_intent("espresso machine price")["intent"],
                         "transactional")

    def test_brand_is_navigational(self):
        self.assertEqual(classify_intent("youtube")["intent"],
                         "navigational")

    def test_plain_topic_defaults_informational(self):
        result = classify_intent("espresso machine maintenance")
        self.assertEqual(result["intent"], "informational")

    def test_near_me_is_local(self):
        result = classify_intent("plumber near me")
        self.assertTrue(result["local"])
        self.assertEqual(result["intent"], "informational")

    def test_non_local_is_not_local(self):
        result = classify_intent("best budget espresso machine")
        self.assertFalse(result["local"])

    def test_question_beats_commercial(self):
        # "how to buy the best laptop" is a how-to first, a buying
        # guide second.
        result = classify_intent("how to buy the best laptop")
        self.assertEqual(result["intent"], "informational")


class TestContentType(unittest.TestCase):
    def test_vs_is_comparison_page(self):
        self.assertEqual(
            content_type_for("commercial", "gaggia vs breville", []),
            "comparison page")

    def test_numbered_headings_are_listicle(self):
        headings = ["1. Breville Bambino", "2. De'Longhi Dedica",
                    "3. Gaggia Classic Pro"]
        self.assertEqual(
            content_type_for("commercial", "best budget espresso machine",
                             headings),
            "listicle")

    def test_transactional_is_product_page(self):
        self.assertEqual(
            content_type_for("transactional", "buy espresso machine", []),
            "product / landing page")

    def test_commercial_is_buying_guide(self):
        self.assertEqual(
            content_type_for("commercial", "best espresso machine", []),
            "buying guide")

    def test_informational_is_how_to_guide(self):
        self.assertEqual(
            content_type_for("informational", "how to fix a tap", []),
            "how-to guide")


if __name__ == "__main__":
    unittest.main()
