"""Search-intent classification for a target keyword.

A brief for "how to fix a leaking tap" and a brief for "buy espresso
machine under $200" are different documents: different content type,
different outline, different call to action. Intent is guessed from the
words in the keyword itself — the same signals Google uses, minus the
search data. It is a heuristic, and the brief says so; the user can
override it with ``--intent`` on the command line.
"""

# Word lists are matched against whole words of the lowercased keyword.
# Order matters: question words win over commercial words, because
# "how to buy the best laptop" is still a how-to article first.

QUESTION_WORDS = {
    "how", "what", "why", "when", "where", "who", "whom", "whose",
    "which", "can", "should", "is", "are", "does", "do",
}

TRANSACTIONAL_WORDS = {
    "buy", "price", "prices", "pricing", "cheap", "cheapest", "discount",
    "deal", "deals", "coupon", "coupons", "order", "shop", "shopping",
    "purchase", "sale", "for sale", "under", "cost", "costs",
}

COMMERCIAL_WORDS = {
    "best", "top", "review", "reviews", "vs", "versus", "compare",
    "comparison", "alternative", "alternatives", "compared", "rating",
    "ratings", "recommend", "recommended", "worth",
}

LOCAL_SIGNALS = {"near me", "nearby", "in my area", "open now"}

# Brand / platform names that usually mean the searcher wants a
# specific site, not information about a topic.
NAVIGATIONAL_WORDS = {
    "amazon", "youtube", "facebook", "instagram", "tiktok", "linkedin",
    "twitter", "reddit", "wikipedia", "ebay", "etsy", "login", "sign in",
    "official", "website", "app", "download",
}

INTENTS = ("informational", "commercial", "transactional", "navigational")


def _words(keyword):
    """Lowercased whole words of a keyword, plus the keyword itself."""
    text = " ".join(keyword.lower().split())
    return set(text.split()), text


def classify_intent(keyword):
    """Return the most likely intent for ``keyword``.

    Returns a dict with the primary intent, a short explanation of the
    signal that decided it, and whether the keyword is local.
    """
    words, text = _words(keyword)
    local = any(signal in text for signal in LOCAL_SIGNALS)

    if words & QUESTION_WORDS or text.startswith(
        ("how ", "what ", "why ", "when ", "where ", "who ", "which ",
         "can ", "should ", "is ", "are ", "does ", "do ")
    ):
        return {
            "intent": "informational",
            "signal": "starts with a question word",
            "local": local,
        }
    if words & NAVIGATIONAL_WORDS:
        return {
            "intent": "navigational",
            "signal": "names a brand, platform or site",
            "local": local,
        }
    if words & TRANSACTIONAL_WORDS:
        return {
            "intent": "transactional",
            "signal": "buying / price words (buy, price, cheap, deal)",
            "local": local,
        }
    if words & COMMERCIAL_WORDS:
        return {
            "intent": "commercial",
            "signal": "comparison words (best, top, review, vs)",
            "local": local,
        }
    return {
        "intent": "informational",
        "signal": "no buying or comparison words — default",
        "local": local,
    }


def content_type_for(intent, keyword, headings):
    """Pick the page format the brief should recommend.

    ``headings`` is a flat list of competitor H2 texts; numbered headings
    ("1. Breville Bambino") are the fingerprint of a listicle.
    """
    _, text = _words(keyword)
    numbered = sum(
        1 for h in headings
        if h.strip()[:2].rstrip(".").isdigit() or h.strip().lower().startswith(
            ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")
        )
    )
    if " vs " in text or " versus " in text:
        return "comparison page"
    if numbered >= 3:
        return "listicle"
    if intent == "transactional":
        return "product / landing page"
    if intent == "commercial":
        return "buying guide"
    if intent == "navigational":
        return "brand / resource page"
    return "how-to guide"
