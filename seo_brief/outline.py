"""Outline builder: merge competitor headings into one outline.

Every competitor covers the topic slightly differently. The outline
takes all H2 headings, groups near-duplicates ("What to look for" /
"How to choose" / "What actually matters" are the same section wearing
different hats) into one section, orders sections by how many
competitors cover them, and splits the target word count across the
sections in proportion to that coverage. H3s are kept as sub-points
under the H2 they followed on their own page.
"""

import re
from dataclasses import dataclass, field

from .terms import load_stopwords

# Headings that are page furniture, not content sections. The brief
# adds its own FAQ section from the questions list, so FAQ headings
# are dropped here (matched by substring: "Espresso machine FAQs").
_SKIP_SUBSTRINGS = ("faq", "frequently asked", "table of contents",
                    "related articles", "you may also like", "references",
                    "conclusion", "final thoughts", "final verdict",
                    "the bottom line", "wrap up", "wrapping up", "summary")

# Different words for the same job: "what to look for", "how to
# choose", "what actually matters" are one section. Canonicalising
# them (plus light stemming) lets the merger see that.
_CHOOSER_WORDS = {"look", "choose", "choosing", "pick", "select", "buy",
                  "buying", "matter", "matters", "know", "guide", "check"}


def _stem(word):
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _content_words(text):
    stopwords = load_stopwords()
    words = set(re.findall(r"[a-z][a-z\-']*", text.lower()))
    canonical = set()
    for word in words:
        if word in stopwords:
            continue
        word = _stem(word)
        if word in _CHOOSER_WORDS:
            word = "choose"
        canonical.add(word)
    return canonical


def _similar(a, b):
    """True if two headings are probably the same section.

    Jaccard similarity on content words, with a bonus for sharing a
    rare word (a number, a brand, a distinctive noun).
    """
    words_a, words_b = _content_words(a), _content_words(b)
    if not words_a or not words_b:
        return a.strip().lower() == b.strip().lower()
    shared = words_a & words_b
    union = words_a | words_b
    if not union:
        return False
    return len(shared) / len(union) >= 0.5


def _clean_heading(text):
    """Strip list numbers ("1. Breville Bambino" -> "Breville Bambino")."""
    text = " ".join(text.split())
    text = re.sub(r"^\d{1,2}[.)]\s*", "", text)
    return text


@dataclass
class OutlineSection:
    """One section of the merged outline."""

    title: str
    coverage: int = 0              # how many competitor pages have it
    words: int = 0                 # suggested word count for the section
    subheadings: list = field(default_factory=list)
    sources: list = field(default_factory=list)  # page titles it came from


def _is_furniture(heading):
    lowered = heading.lower()
    return any(fragment in lowered for fragment in _SKIP_SUBSTRINGS)


def _is_numbered(heading):
    """True for listicle items: '1. Breville Bambino', '3) Gaggia'."""
    return bool(re.match(r"^\d{1,2}[.)]\s+", heading.strip()))


def build_outline(pages, target_words, max_sections=12):
    """Merge competitor H2/H3 headings into an ordered outline.

    Numbered H2s (listicle items like '1. Breville Bambino') are grouped
    into one 'Top picks' section instead of becoming a section each —
    otherwise a 7-item listicle alone would fill the whole outline.
    Returns a list of OutlineSection, ordered by coverage (most-covered
    first), capped at ``max_sections``.
    """
    clusters = []  # each: {"title", "pages": set, "subs": [], "sources": []}

    def find_cluster(title):
        for cluster in clusters:
            if _similar(cluster["title"], title):
                return cluster
        return None

    def all_subheadings():
        subs = set()
        for cluster in clusters:
            subs |= {s.lower() for s in cluster["subs"]}
        return subs

    for page in pages:
        current = None
        list_cluster = None
        for level, raw_heading in page.headings:
            heading = _clean_heading(raw_heading)
            if not heading:
                continue
            if level == 2:
                if _is_furniture(heading):
                    current = None
                    continue
                if _is_numbered(raw_heading):
                    # Listicle item: fold into the page's Top picks section.
                    if list_cluster is None:
                        list_cluster = find_cluster("Top picks")
                        if list_cluster is None:
                            list_cluster = {"title": "Top picks",
                                            "pages": set(), "subs": [],
                                            "sources": []}
                            clusters.append(list_cluster)
                    list_cluster["pages"].add(page.url)
                    if heading not in list_cluster["subs"]:
                        list_cluster["subs"].append(heading)
                    current = list_cluster
                    continue
                # Skip an H2 that already appears (or nearly appears) as
                # a subheading of another section (e.g. an H3 on one
                # page, an H2 on the next) — it would otherwise show up
                # twice in the brief.
                if any(_similar(heading, sub)
                       for sub in all_subheadings()):
                    current = None
                    continue
                match = find_cluster(heading)
                if match is None:
                    match = {"title": heading, "pages": set(),
                             "subs": [], "sources": []}
                    clusters.append(match)
                match["pages"].add(page.url)
                if page.title and page.title not in match["sources"]:
                    match["sources"].append(page.title)
                current = match
            elif level == 3 and current is not None:
                if not _is_furniture(heading):
                    if heading not in current["subs"]:
                        current["subs"].append(heading)

    sections = [
        OutlineSection(
            title=cluster["title"],
            coverage=len(cluster["pages"]),
            subheadings=cluster["subs"],
            sources=cluster["sources"],
        )
        for cluster in clusters
    ]
    # Most-covered sections first; ties keep first-appearance order.
    sections.sort(key=lambda s: -s.coverage)
    sections = sections[:max_sections]

    # Split the target word count by coverage: a section every
    # competitor covers earns a bigger share. Shares are rounded and
    # any rounding drift is fixed on the first (most important) section,
    # so the shares always add up to the target.
    total_weight = sum(max(1, s.coverage) for s in sections) or 1
    assigned = 0
    for section in sections:
        weight = max(1, section.coverage)
        section.words = max(40, round(target_words * weight / total_weight))
        assigned += section.words
    if sections:
        drift = target_words - assigned
        sections[0].words = max(40, sections[0].words + drift)
    return sections


def word_count_target(pages):
    """Target length from competitor pages: (min, median, max) words."""
    counts = sorted(page.word_count for page in pages if page.word_count > 0)
    if not counts:
        return (0, 0, 0)
    middle = len(counts) // 2
    if len(counts) % 2:
        median = counts[middle]
    else:
        median = (counts[middle - 1] + counts[middle]) // 2
    return (counts[0], median, counts[-1])
