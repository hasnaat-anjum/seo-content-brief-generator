"""Must-include terms: what competitors all talk about, you should too.

The idea is simple TF-IDF thinking without the maths degree: a word
that shows up on every competitor page about your topic is part of the
topic; a word that shows up once is a one-off. Terms are ranked by how
many competitor pages use them, then by how often, and single words and
two-word phrases are both counted — "milk frother" is one idea, not two.
Stopwords and the seed keyword itself are filtered out: the brief tells
you what else to cover, not what you already know.
"""

import json
import math
import os
import re
from collections import Counter

_WORD_RE = re.compile(r"[a-z][a-z\-']*")

# Fallback stopwords if data/stopwords.txt cannot be found.
_FALLBACK_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "for",
    "with", "by", "at", "from", "as", "is", "are", "was", "were", "be",
    "been", "it", "its", "this", "that", "these", "those", "you", "your",
    "we", "our", "they", "their", "he", "she", "his", "her", "not", "no",
    "can", "will", "would", "should", "how", "what", "why", "when",
    "where", "which", "who", "more", "most", "also", "than", "then",
    "into", "about", "over", "under", "after", "before", "between",
}


def load_stopwords():
    """Load data/stopwords.txt; fall back to the built-in short list."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, "data", "stopwords.txt")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            words = {line.strip() for line in handle if line.strip()}
        if words:
            return words
    except OSError:
        pass
    return set(_FALLBACK_STOPWORDS)


# Words too generic to be useful must-include terms. They show up on
# every page about everything ("good coffee", "make sure", "buy now")
# and would crowd out the real topic words.
GENERIC_WORDS = {
    "good", "great", "best", "make", "makes", "made", "buy", "get", "got",
    "use", "used", "using", "one", "two", "three", "also", "much", "many",
    "well", "really", "first", "new", "way", "thing", "things", "dollars",
    "spend", "spent", "take", "takes", "need", "needs", "want", "like",
    "just", "even", "still", "back", "put", "keep", "go", "goes", "come",
    "comes", "see", "look", "looks", "work", "works", "help", "helps",
    "right", "easy", "simple", "sure", "lot", "bit", "top", "better",
}


def _stem(word):
    """Light stemming: strip a trailing 's' from longer words so
    'machines' and 'machine' count as the same word."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def tokenize(text):
    """Lowercased content words of a text, stopwords removed."""
    stopwords = load_stopwords()
    return [w for w in _WORD_RE.findall(text.lower()) if w not in stopwords]


def _ngrams(tokens, n):
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def top_terms(pages, seed, limit=15):
    """Rank terms across competitor pages.

    Returns a list of dicts: {term, pages, count, score}. ``score`` is
    pages-covered weighted by log frequency, so a term on all 3 pages
    beats a term repeated 20 times on one page. Seed words are excluded.
    """
    seed_words = {_stem(w) for w in _WORD_RE.findall(seed.lower())}
    doc_count = Counter()   # term -> number of pages using it
    total_count = Counter()  # term -> total mentions
    for page in pages:
        tokens = tokenize(page.text)
        terms = set(_ngrams(tokens, 1)) | set(_ngrams(tokens, 2))
        for term in terms:
            doc_count[term] += 1
        for term in _ngrams(tokens, 1) + _ngrams(tokens, 2):
            total_count[term] += 1

    ranked = []
    for term, pages_covered in doc_count.items():
        words = term.split()
        # Skip generic filler words, the seed itself (including plurals
        # like "machines" when the seed says "machine"), and any term
        # made only of seed words.
        if len(words) == 1 and words[0] in GENERIC_WORDS:
            continue
        if all(w in GENERIC_WORDS for w in words):
            continue
        if all(_stem(w) in seed_words for w in words):
            continue
        # Skip two-word phrases that are just a stopword + word, and
        # single words shorter than 3 letters (units, abbreviations).
        if len(term) < 3:
            continue
        score = pages_covered * (1 + math.log1p(total_count[term]))
        ranked.append({
            "term": term,
            "pages": pages_covered,
            "count": total_count[term],
            "score": round(score, 2),
        })
    ranked.sort(key=lambda item: (-item["score"], -item["pages"], item["term"]))
    return ranked[:limit]


def term_coverage(text, terms):
    """Which of ``terms`` (list of term strings) appear in ``text``.

    Matching is on whole words only: the term "bar" must not match
    "barista". Returns (found, missing): lists of term strings.
    """
    lowered = " " + " ".join(text.lower().split()) + " "
    found, missing = [], []
    for term in terms:
        if " " + " ".join(term.lower().split()) + " " in lowered:
            found.append(term)
        else:
            missing.append(term)
    return found, missing


def load_niches():
    """Starter seed keywords per niche from data/niches.json."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, "data", "niches.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)["niches"]
    except (OSError, ValueError, KeyError):
        return []
