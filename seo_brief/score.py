"""Draft scoring: how well does a draft follow its brief?

A draft is scored 0-100 against the brief it was written from: keyword
placement (title, first heading, first 100 words), outline coverage
(did it actually write the sections the brief asked for), length vs the
target, readability (Flesch reading ease — plain English scores higher),
and must-include terms. Every point lost comes with a concrete fix, so
the score is a to-do list, not a judgement.
"""

import re

from .terms import term_coverage

# Flesch reading ease bands, as used by readability checkers.
READABILITY_BANDS = [
    (90, "Very easy — a 5th grader can read it"),
    (80, "Easy — conversational plain English"),
    (70, "Fairly easy"),
    (60, "Plain English — the target for web content"),
    (50, "Fairly difficult"),
    (30, "Difficult — long sentences and heavy words"),
    (0, "Very difficult — rewrite in shorter sentences"),
]


def _syllables(word):
    """Rough syllable count: vowel groups, minus a trailing silent e."""
    word = word.lower().strip()
    if not word:
        return 0
    groups = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e") and groups > 1:
        groups -= 1
    return max(1, groups)


def flesch_reading_ease(text):
    """Flesch reading ease 0-100 (higher = easier). Returns (score, label)."""
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    words = re.findall(r"[A-Za-z][A-Za-z\-']*", text)
    if not sentences or not words:
        return (0.0, "No readable text found")
    words_per_sentence = len(words) / len(sentences)
    syllables_per_word = sum(_syllables(w) for w in words) / len(words)
    score = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word
    score = max(0.0, min(100.0, score))
    label = next(label for bound, label in READABILITY_BANDS if score >= bound)
    return (round(score, 1), label)


def _headings_of(draft):
    """Markdown headings (level, text) from a draft."""
    headings = []
    for line in draft.splitlines():
        match = re.match(r"^(#{1,3})\s+(.*)", line.strip())
        if match:
            headings.append((len(match.group(1)), match.group(2).strip()))
    return headings


def _grade(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def score_draft(draft, brief):
    """Score ``draft`` (Markdown/text) against a Brief. Returns a dict."""
    keyword = brief.keyword.lower()
    seed_words = [w for w in re.findall(r"[a-z]+", keyword)]
    words = re.findall(r"[A-Za-z][A-Za-z\-']*", draft)
    word_count = len(words)
    lowered = draft.lower()
    headings = _headings_of(draft)
    heading_text = " ".join(text for _, text in headings).lower()
    first_100 = " ".join(words[:100]).lower()

    checks = []
    score = 0

    # 1. Keyword in the title / first heading (15 points).
    first_heading = headings[0][1].lower() if headings else ""
    if keyword in first_heading:
        score += 15
        checks.append(("Keyword in the title/first heading", 15, 15, ""))
    elif all(w in first_heading for w in seed_words):
        score += 10
        checks.append(("Keyword in the title/first heading", 10, 15,
                       "Title has the seed words but not the exact phrase"))
    else:
        checks.append(("Keyword in the title/first heading", 0, 15,
                       "Put the exact keyword in the H1 title"))

    # 2. Keyword in the first 100 words (10 points).
    if keyword in first_100:
        score += 10
        checks.append(("Keyword in the first 100 words", 10, 10, ""))
    else:
        checks.append(("Keyword in the first 100 words", 0, 10,
                       "Mention the keyword in the opening paragraph"))

    # 3. Outline coverage (30 points): each brief section whose key
    # words appear in the draft's headings.
    outline = brief.outline
    covered = 0
    missing_sections = []
    for section in outline:
        section_words = set(re.findall(
            r"[a-z][a-z\-']*", section["title"].lower()))
        section_words -= {"the", "a", "an", "and", "for", "of", "to", "in"}
        if section_words and len(section_words & set(
                re.findall(r"[a-z][a-z\-']*", heading_text))) >= max(
                    1, len(section_words) // 2):
            covered += 1
        else:
            missing_sections.append(section["title"])
    outline_points = round(30 * covered / len(outline)) if outline else 30
    score += outline_points
    checks.append((
        "Outline coverage (%d of %d sections)" % (covered, len(outline)),
        outline_points, 30,
        "" if not missing_sections else
        "Missing sections: " + "; ".join(missing_sections[:3]),
    ))

    # 4. Length vs target (15 points): full marks at 90-110% of target.
    target = brief.target_words or 800
    ratio = word_count / target if target else 0
    if 0.9 <= ratio <= 1.1:
        length_points = 15
        length_fix = ""
    elif 0.7 <= ratio < 0.9 or 1.1 < ratio <= 1.3:
        length_points = 10
        length_fix = "Aim for %d words (currently %d)." % (target, word_count)
    elif ratio >= 0.5:
        length_points = 5
        length_fix = "Aim for %d words (currently %d)." % (target, word_count)
    else:
        length_points = 0
        length_fix = "Draft is much shorter than the %d-word target." % target
    score += length_points
    checks.append(("Length (%d of %d target words)"
                   % (word_count, target), length_points, 15, length_fix))

    # 5. Readability (15 points): Flesch 60+ is plain English.
    ease, ease_label = flesch_reading_ease(draft)
    if ease >= 60:
        read_points = 15
        read_fix = ""
    elif ease >= 50:
        read_points = 10
        read_fix = "Shorten some sentences — aim for Flesch 60+."
    elif ease >= 30:
        read_points = 5
        read_fix = "Hard to read (Flesch %.0f) — shorter sentences, simpler words." % ease
    else:
        read_points = 0
        read_fix = "Very hard to read (Flesch %.0f) — rewrite in plain English." % ease
    score += read_points
    checks.append(("Readability (Flesch %.0f — %s)"
                   % (ease, ease_label), read_points, 15, read_fix))

    # 6. Must-include terms (15 points): share of the brief's top terms
    # that appear in the draft.
    top_term_strings = [t["term"] for t in brief.must_include_terms[:10]]
    found, missing = term_coverage(draft, top_term_strings)
    term_points = round(15 * len(found) / len(top_term_strings)) \
        if top_term_strings else 15
    score += term_points
    checks.append((
        "Must-include terms (%d of %d used)"
        % (len(found), len(top_term_strings)),
        term_points, 15,
        "" if not missing else "Missing terms: " + ", ".join(missing[:5]),
    ))

    fixes = [fix for _, _, _, fix in checks if fix]
    return {
        "score": score,
        "grade": _grade(score),
        "word_count": word_count,
        "target_words": target,
        "readability": ease,
        "readability_label": ease_label,
        "checks": [
            {"name": name, "points": points, "max": maximum, "fix": fix}
            for name, points, maximum, fix in checks
        ],
        "fixes": fixes,
    }
