"""Tests for the brief store (atomic JSON + .bak)."""

import json
import os
import tempfile
import unittest

from seo_brief.brief import build_brief
from seo_brief.store import (StoreError, delete_brief, get_brief,
                             list_briefs, load_store, save_brief, save_store)
from tests import load_example_pages

SEED = "best budget espresso machine for beginners"


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = os.path.join(self.tmp.name, "briefs.json")

    def tearDown(self):
        self.tmp.cleanup()


class TestStoreRoundTrip(StoreTestCase):
    def test_save_get_list_delete(self):
        brief = build_brief(SEED, load_example_pages())
        brief_id = save_brief(brief, self.store)
        self.assertEqual(brief_id, brief.id)
        loaded = get_brief(brief_id, self.store)
        self.assertEqual(loaded["keyword"], SEED)
        self.assertEqual(len(list_briefs(self.store)), 1)
        self.assertTrue(delete_brief(brief_id, self.store))
        self.assertEqual(list_briefs(self.store), [])
        self.assertFalse(delete_brief(brief_id, self.store))

    def test_missing_store_is_empty(self):
        self.assertEqual(load_store(self.store), {})
        self.assertIsNone(get_brief("nope", self.store))

    def test_second_save_keeps_backup(self):
        brief = build_brief(SEED, load_example_pages())
        save_brief(brief, self.store)
        with open(self.store, encoding="utf-8") as handle:
            first = handle.read()
        save_brief(brief, self.store)
        backup = self.store + ".bak"
        self.assertTrue(os.path.exists(backup))
        with open(backup, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), first)

    def test_corrupt_store_raises(self):
        with open(self.store, "w", encoding="utf-8") as handle:
            handle.write("{not json")
        with self.assertRaises(StoreError):
            load_store(self.store)

    def test_non_object_store_raises(self):
        save_store(["not", "a", "dict"], self.store)
        with self.assertRaises(StoreError):
            load_store(self.store)

    def test_list_newest_first(self):
        first = build_brief("espresso machine", [])
        second = build_brief("coffee grinder", [])
        second.created = "2026-11-25"
        save_brief(first, self.store)
        save_brief(second, self.store)
        listed = list_briefs(self.store)
        self.assertEqual(listed[0]["keyword"], "coffee grinder")
        self.assertEqual(listed[1]["keyword"], "espresso machine")


if __name__ == "__main__":
    unittest.main()
