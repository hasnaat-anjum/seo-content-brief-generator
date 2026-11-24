"""Question keywords: the "People also ask" box, generated locally.

Google's "People also ask" section is a goldmine for briefs — every
question is a heading your article can answer. This module builds the
same list from templates applied to the seed keyword. Templates use the
core seed (a leading "best" and a trailing "for beginners" are stripped
first, or the templates would read "What is the best best budget
espresso machine?") and an article ("a"/"an") so the questions read
like something a person would actually type.
"""

# Seeds that start with one of these words are verb phrases ("start a
# food blog"), so "How to <seed>?" is a natural question for them.
_VERB_STARTERS = {
    "start", "make", "build", "grow", "learn", "write", "create", "fix",
    "improve", "lose", "save", "sell", "cook", "train", "plan", "design",
    "launch", "run", "open", "become",
}

# Templates for verb-phrase seeds ("how to start a food blog"):
# {topic} is the action, e.g. "start a food blog".
_VERB_TEMPLATES = [
    "How to {topic}?",
    "How to {topic} for beginners?",
    "What is the best way to {topic}?",
    "How long does it take to {topic}?",
    "How much does it cost to {topic}?",
    "What do I need to {topic}?",
    "Can I {topic} without experience?",
    "What are the most common mistakes when you {topic}?",
    "How do I {topic} step by step?",
    "Is it worth it to {topic}?",
]

# (template, ) — {a} is "a"/"an", {core} is the core seed.
_TEMPLATES = [
    "How to choose {a} {core}?",
    "What is {a} {core}?",
    "What is the best {core}?",
    "How much does {a} {core} cost?",
    "Is {a} {core} worth it?",
    "How long does {a} {core} last?",
    "Why buy {a} {core}?",
    "When should you buy {a} {core}?",
    "Where can I buy {a} {core}?",
    "{core} vs alternatives: which is better?",
    "What should I look for in {a} {core}?",
    "Can beginners use {a} {core}?",
    "What are common {core} mistakes to avoid?",
    "How do I choose {a} {core}?",
    "Do I need {a} {core}?",
]


def core_seed(keyword):
    """The seed stripped down to its topic.

    A leading question ("how to ", "what is ") is removed first, then a
    leading "best" and a trailing "for beginners" — the templates add
    those words back themselves, or "What is the best best ..." results.
    """
    words = keyword.lower().split()
    if words[:2] == ["how", "to"]:
        words = words[2:]
    elif words[:3] in (["how", "do", "i"], ["how", "can", "i"]):
        words = words[3:]
    elif words[:2] in (["what", "is"], ["what", "are"]):
        words = words[2:]
    if words and words[0] == "best":
        words = words[1:]
    if len(words) >= 2 and words[-2:] == ["for", "beginners"]:
        words = words[:-2]
    return " ".join(words)


def is_verb_phrase(keyword):
    """True if the seed is an action ("start a food blog"), not a thing."""
    words = core_seed(keyword).split()
    return bool(words) and words[0] in _VERB_STARTERS


def _article(core):
    return "an" if core[:1] in "aeiou" else "a"


def generate_questions(seed, limit=10):
    """Question keywords built from templates around the seed keyword."""
    seed = " ".join(seed.lower().split())
    core = core_seed(seed) or seed
    questions = []
    if is_verb_phrase(seed):
        for template in _VERB_TEMPLATES:
            question = template.format(topic=core)
            if question not in questions:
                questions.append(question)
            if len(questions) >= limit:
                break
    else:
        article = _article(core)
        for template in _TEMPLATES:
            question = template.format(a=article, core=core)
            if question not in questions:
                questions.append(question)
            if len(questions) >= limit:
                break
    return questions


def merge_questions(generated, from_competitors, limit=10):
    """Competitor questions first (they are proven to rank), then generated."""
    merged, seen = [], set()
    for question in list(from_competitors) + list(generated):
        key = question.lower().strip()
        if key and key not in seen:
            seen.add(key)
            merged.append(question)
        if len(merged) >= limit:
            break
    return merged
