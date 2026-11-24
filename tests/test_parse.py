"""Tests for fetching and parsing competitor pages."""

import unittest

from seo_brief.parse import extract_questions, parse_html
from tests import load_example_pages


class TestParseHtml(unittest.TestCase):
    SAMPLE = """
    <html><head><title>Test Page Title</title>
    <meta name="description" content="A short test description.">
    <style>.hidden { display: none; }</style>
    <script>var secret = 1;</script>
    </head><body>
    <h1>Main Heading</h1>
    <p>First paragraph with some words.</p>
    <h2>Section One</h2>
    <p>More body text here.</p>
    <h3>Sub Section</h3>
    <p>Final words.</p>
    </body></html>
    """

    def test_title_and_meta(self):
        page = parse_html(self.SAMPLE, "https://example.com/test")
        self.assertEqual(page.title, "Test Page Title")
        self.assertEqual(page.meta_description, "A short test description.")

    def test_headings_extracted_with_levels(self):
        page = parse_html(self.SAMPLE)
        self.assertIn((1, "Main Heading"), page.headings)
        self.assertIn((2, "Section One"), page.headings)
        self.assertIn((3, "Sub Section"), page.headings)

    def test_script_and_style_text_excluded(self):
        page = parse_html(self.SAMPLE)
        self.assertNotIn("secret", page.text)
        self.assertNotIn("hidden", page.text)
        self.assertIn("First paragraph", page.text)

    def test_word_count_counts_body_text(self):
        page = parse_html(self.SAMPLE)
        self.assertGreater(page.word_count, 10)

    def test_h2s_property(self):
        page = parse_html(self.SAMPLE)
        self.assertEqual(page.h2s, ["Section One"])

    def test_missing_title_is_empty(self):
        page = parse_html("<html><body><p>No title here.</p></body></html>")
        self.assertEqual(page.title, "")
        self.assertEqual(page.meta_description, "")


class TestExamplePages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = load_example_pages()

    def test_three_pages_loaded(self):
        self.assertEqual(len(self.pages), 3)

    def test_titles_present(self):
        titles = [p.title for p in self.pages]
        self.assertIn("Best Budget Espresso Machines for Beginners (2026)",
                      titles)
        self.assertIn("7 Cheap Espresso Machines That Actually Make "
                      "Great Coffee", titles)

    def test_word_counts_are_realistic(self):
        for page in self.pages:
            self.assertGreater(page.word_count, 400)
            self.assertLess(page.word_count, 1500)

    def test_headings_present(self):
        self.assertGreater(len(self.pages[0].headings), 5)
        self.assertIn("What to look for in a budget espresso machine",
                      self.pages[0].h2s)

    def test_extract_questions_only_question_marks(self):
        questions = extract_questions(self.pages)
        self.assertTrue(all(q.endswith("?") for q in questions))
        self.assertIn("What is the best budget espresso machine "
                      "for beginners?", questions)
        # A heading that starts with "What" but is not a question.
        self.assertNotIn("What to look for in a budget espresso machine",
                         questions)


if __name__ == "__main__":
    unittest.main()
