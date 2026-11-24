"""Tests for question-keyword generation."""

import unittest

from seo_brief.questions import (core_seed, generate_questions,
                                 is_verb_phrase, merge_questions)


class TestCoreSeed(unittest.TestCase):
    def test_strips_best_and_for_beginners(self):
        self.assertEqual(
            core_seed("best budget espresso machine for beginners"),
            "budget espresso machine")

    def test_strips_how_to(self):
        self.assertEqual(core_seed("how to start a food blog"),
                         "start a food blog")

    def test_plain_seed_unchanged(self):
        self.assertEqual(core_seed("espresso machine"), "espresso machine")


class TestIsVerbPhrase(unittest.TestCase):
    def test_how_to_seed_is_verb_phrase(self):
        self.assertTrue(is_verb_phrase("how to start a food blog"))

    def test_bare_verb_seed_is_verb_phrase(self):
        self.assertTrue(is_verb_phrase("start a food blog"))

    def test_noun_seed_is_not_verb_phrase(self):
        self.assertFalse(is_verb_phrase("best budget espresso machine"))


class TestGenerateQuestions(unittest.TestCase):
    def test_noun_seed_questions_read_naturally(self):
        questions = generate_questions(
            "best budget espresso machine for beginners")
        self.assertIn("How to choose a budget espresso machine?", questions)
        self.assertIn("What is the best budget espresso machine?", questions)
        self.assertIn("How much does a budget espresso machine cost?",
                      questions)
        # No doubled "best" and no "How to best ..." nonsense.
        for question in questions:
            self.assertNotIn("best best", question)
            self.assertNotIn("How to best", question)

    def test_verb_seed_questions_read_naturally(self):
        questions = generate_questions("how to start a food blog")
        self.assertIn("How to start a food blog?", questions)
        self.assertIn("What is the best way to start a food blog?",
                      questions)
        self.assertIn("How much does it cost to start a food blog?",
                      questions)
        for question in questions:
            self.assertNotIn("a how to", question)

    def test_limit_respected(self):
        self.assertEqual(
            len(generate_questions("espresso machine", limit=3)), 3)

    def test_article_an_for_vowels(self):
        questions = generate_questions("espresso machine")
        self.assertIn("What is an espresso machine?", questions)


class TestMergeQuestions(unittest.TestCase):
    def test_competitor_questions_first(self):
        merged = merge_questions(
            ["How to choose a budget espresso machine?"],
            ["What is the best budget espresso machine?"])
        self.assertEqual(merged[0],
                         "What is the best budget espresso machine?")

    def test_duplicates_removed(self):
        merged = merge_questions(
            ["How to choose a budget espresso machine?"],
            ["How to choose a budget espresso machine?"])
        self.assertEqual(len(merged), 1)

    def test_limit_respected(self):
        merged = merge_questions(["Q%d?" % i for i in range(5)],
                                 ["R%d?" % i for i in range(5)], limit=4)
        self.assertEqual(len(merged), 4)


if __name__ == "__main__":
    unittest.main()
