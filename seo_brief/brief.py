"""Brief assembly: turn competitor pages into a writer's brief.

A brief is the document a writer opens before writing: what the page is
for (intent + content type), how long it should be (from real competitor
lengths), what it must cover (the merged outline + must-include terms +
questions), what to call it (titles + meta descriptions), and how to
make it trustworthy (E-E-A-T checklist + CTA). Every number in it is
measured from the competitor pages or labelled as a suggestion — the
brief never invents search volume or ranking promises.
"""

import re
from dataclasses import asdict, dataclass, field
from datetime import date

from .intent import classify_intent, content_type_for
from .outline import build_outline, word_count_target
from .parse import extract_questions
from .questions import (core_seed, generate_questions, is_verb_phrase,
                        merge_questions)
from .terms import term_coverage, tokenize, top_terms

_SMALL_WORDS = {"a", "an", "the", "and", "or", "for", "of", "to", "in",
                "on", "with", "vs", "by", "at"}


def _title_case(text):
    """Title-case a keyword, keeping small words lowercase mid-title."""
    words = text.split()
    titled = []
    for i, word in enumerate(words):
        if i > 0 and word.lower() in _SMALL_WORDS:
            titled.append(word.lower())
        else:
            titled.append(word[:1].upper() + word[1:])
    return " ".join(titled)


def _fit(text, limit):
    """Shorten a title/meta to ``limit`` chars, cutting at a word edge."""
    if len(text) <= limit:
        return text
    cut = text[:limit - 3].rsplit(" ", 1)[0]
    return cut + "..."


def _core_seed(keyword):
    """The seed without a leading 'best' and a trailing 'for beginners'.

    Title templates add those words themselves; without this step a seed
    like 'best budget espresso machine for beginners' would produce
    'Best Best Budget Espresso Machine for Beginners for Beginners'.
    """
    return core_seed(keyword)


def title_options(keyword):
    """Five title options containing the seed, each 60 chars or fewer.

    Long seeds are the norm in SEO, so templates are built from the
    core seed and filtered by length; the title-cased seed itself is
    always available as a fallback, so the list is never empty.
    """
    seed = _title_case(keyword)
    core = _title_case(_core_seed(keyword))
    year = date.today().year
    if is_verb_phrase(keyword):
        # Action seeds ("how to start a food blog") get how-to titles;
        # "Best <action> for Beginners" would read as nonsense.
        candidates = [
            "%s: The Complete Guide (%d)" % (seed, year),
            "How to %s: A Beginner's Guide" % core,
            "%s — A Step-by-Step Guide" % seed,
            "%s Explained: A Simple Guide" % seed,
            "How to %s in %d" % (core, year),
            seed,
        ]
    else:
        candidates = [
            "%s: The Complete Guide (%d)" % (seed, year),
            "Best %s for Beginners" % core,
            "How to Choose %s: A Beginner's Guide" % core,
            "%s: A Beginner's Guide" % core,
            "%s — Top Picks for Beginners" % core,
            "%s — What to Know Before You Buy" % seed,
            "%s: 7 Things Nobody Tells Beginners" % seed,
            "The Best %s, Tested and Compared (%d)" % (core, year),
            "%s Explained: A Simple Guide" % seed,
            "The Complete %s Guide (%d)" % (core, year),
            seed,
        ]
    options = []
    for candidate in candidates:
        if len(candidate) <= 60 and candidate not in options:
            options.append(candidate)
        if len(options) == 5:
            break
    return options


def meta_options(keyword):
    """Three meta descriptions, each 160 chars or fewer."""
    seed = keyword.lower()
    candidates = [
        ("Looking for %s? Compare the best options, what to check "
         "before you buy, and the mistakes beginners make — in one guide."
         % seed),
        ("Our %s guide covers the top picks, prices and what actually "
         "matters, so you can buy once and buy right." % seed),
        ("Everything you need to know about %s: how to choose, what to "
         "avoid, and the best options for beginners." % seed),
    ]
    return [_fit(text, 160) for text in candidates]


def _score_competitor(page, seed):
    """Score a competitor 0-30 on depth, formatting and on-page SEO."""
    words = page.word_count
    depth = 10 if words >= 1500 else 8 if words >= 1000 else \
        6 if words >= 600 else 4 if words >= 300 else 2
    h2_count = len(page.h2s)
    formatting = 10 if h2_count >= 6 else 8 if h2_count >= 4 else \
        6 if h2_count >= 2 else 4 if h2_count >= 1 else 2
    seo = 0
    seed_words = set(re.findall(r"[a-z]+", seed.lower()))
    title_words = set(re.findall(r"[a-z]+", page.title.lower()))
    if seed_words & title_words:
        seo += 5
    if page.meta_description:
        seo += 3
    if any(level == 1 for level, _ in page.headings):
        seo += 2
    return {"depth": depth, "formatting": formatting, "seo": seo,
            "total": depth + formatting + seo}


def _eeat_checklist(content_type):
    """Trust signals the draft needs, tailored to the page format."""
    base = [
        "Author byline with a real name — and a line saying why this "
        "author knows the topic.",
        "Publish date and 'last updated' date, both visible on the page.",
        "Cite sources with links wherever a fact, price or claim appears.",
        "Answer every question in the brief's question list, in a short "
        "FAQ section near the end.",
        "Original photos or screenshots where possible — not stock only.",
    ]
    if content_type in ("buying guide", "listicle", "comparison page"):
        base += [
            "Hands-on testing notes: what was actually tried, for how "
            "long, and what happened.",
            "Prices checked on a named date — and say so in the text.",
            "If any link earns commission, say so in one clear sentence.",
        ]
    elif content_type == "how-to guide":
        base += [
            "Every step tested by the writer, in order, before publishing.",
            "A tools / materials list up front, with anything optional "
            "marked as optional.",
            "Warn readers before any step that costs money or can go wrong.",
        ]
    return base


def _question_answered(question, pages):
    """True if some competitor heading covers the same question.

    Compared on content words (Jaccard >= 0.5), not exact text: a
    competitor heading 'How to choose a cheap espresso machine' does
    answer the question 'How to choose a budget espresso machine?'.
    """
    question_words = set(tokenize(question))
    if not question_words:
        return True
    for page in pages:
        for _, heading in page.headings:
            heading_words = set(tokenize(heading))
            if not heading_words:
                continue
            shared = question_words & heading_words
            if len(shared) / len(question_words | heading_words) >= 0.5:
                return True
    return False


def _cta_for(intent):
    return {
        "transactional": "Put a clear buy CTA after the top pick: price, "
                         "stock note and a link to the retailer.",
        "commercial": "End every option with a one-line verdict and a link; "
                      "close with a comparison table and one recommended pick.",
        "informational": "Close with a next step: a related guide, a free "
                         "checklist download, or a newsletter signup.",
        "navigational": "Link straight to the official page and add a short "
                        "'what you get' summary above it.",
    }.get(intent, "Close with one clear next step for the reader.")


def _internal_link_suggestions(keyword, terms, own_pages, limit=5):
    """Rank the writer's own pages by overlap with the topic terms."""
    if not own_pages:
        return []
    topic_words = set(re.findall(r"[a-z][a-z\-']*", keyword.lower()))
    for term in terms:
        topic_words |= set(term["term"].split())
    scored = []
    for page in own_pages:
        title = page.get("title", "")
        words = set(re.findall(r"[a-z][a-z\-']*", title.lower()))
        overlap = sorted(topic_words & words)
        if overlap:
            scored.append({
                "title": title,
                "url": page.get("url", ""),
                "matched_words": overlap,
                "score": len(overlap),
            })
    scored.sort(key=lambda item: (-item["score"], item["title"]))
    return scored[:limit]


@dataclass
class Brief:
    """A complete content brief, ready to hand to a writer."""

    id: str
    keyword: str
    intent: str
    intent_signal: str
    local: bool
    content_type: str
    target_words: int
    word_range: dict
    titles: list
    meta_descriptions: list
    outline: list            # list of dicts: title, coverage, words, subheadings
    must_include_terms: list  # list of dicts: term, pages, count
    questions: list
    competitor_table: list    # list of dicts: url, title, words, headings, score
    gaps: list                # opportunities competitors missed
    internal_links: list
    eeat_checklist: list
    call_to_action: str
    created: str = ""
    notes: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


def build_brief(keyword, pages, own_pages=None, intent_override=None):
    """Build a Brief from a keyword and parsed competitor pages.

    ``pages`` may include pages with ``fetch_error`` set — those are
    reported in notes and excluded from the analysis. At least one
    usable page is required; with none, the brief is built from the
    keyword alone and says so in its notes.
    """
    usable = [p for p in pages if not p.fetch_error and p.word_count > 0]
    failed = [p for p in pages if p.fetch_error]
    notes = []
    if failed:
        notes.append(
            "%d competitor page(s) could not be fetched and were left out: %s"
            % (len(failed), ", ".join(p.url for p in failed)))
    if not usable:
        notes.append(
            "No competitor pages could be read, so this brief is built "
            "from the keyword alone — add --url or --file pages for a "
            "data-driven brief.")

    info = classify_intent(keyword)
    intent = intent_override or info["intent"]
    all_h2s = [h for p in usable for h in p.h2s]
    content_type = content_type_for(intent, keyword, all_h2s)
    low, median, high = word_count_target(usable)
    target = median or 800
    # Round the target to the nearest 50 so writers get a round number.
    target = int(round(target / 50.0) * 50) or 800

    outline_sections = build_outline(usable, target) if usable else []
    terms = top_terms(usable, keyword) if usable else []
    competitor_questions = extract_questions(usable)
    questions = merge_questions(
        generate_questions(keyword), competitor_questions)

    # Gaps: outline sections few competitors cover, and questions no
    # competitor answers — the openings this article can win. Capped at
    # five so the brief stays a to-do list, not a wall of text.
    gaps = []
    for section in outline_sections:
        if section.coverage == 1 and len(usable) >= 3:
            gaps.append("Only 1 of %d competitors covers '%s' — covering "
                        "it well is an easy win." % (len(usable), section.title))
        if len(gaps) >= 3:
            break
    for question in questions:
        if not _question_answered(question, usable):
            gaps.append("No competitor answers '%s' directly — answer it "
                        "in your FAQ." % question)
        if len(gaps) >= 5:
            break

    slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-") or "brief"
    brief_id = "%s-%s" % (slug, date.today().strftime("%Y%m%d"))

    return Brief(
        id=brief_id,
        keyword=keyword,
        intent=intent,
        intent_signal=info["signal"],
        local=info["local"],
        content_type=content_type,
        target_words=target,
        word_range={"min": low, "median": median, "max": high},
        titles=title_options(keyword),
        meta_descriptions=meta_options(keyword),
        outline=[{
            "title": s.title, "coverage": s.coverage, "words": s.words,
            "subheadings": s.subheadings,
        } for s in outline_sections],
        must_include_terms=terms,
        questions=questions,
        competitor_table=[{
            "url": p.url,
            "title": p.title or "(no title found)",
            "words": p.word_count,
            "headings": len(p.headings),
            "score": _score_competitor(p, keyword)["total"],
        } for p in usable],
        gaps=gaps,
        internal_links=_internal_link_suggestions(
            keyword, terms, own_pages or []),
        eeat_checklist=_eeat_checklist(content_type),
        call_to_action=_cta_for(intent),
        created=date.today().isoformat(),
        notes=notes,
    )
