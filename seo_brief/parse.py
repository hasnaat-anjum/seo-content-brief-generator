"""Fetch and parse competitor pages with the standard library only.

Fetching is deliberately polite and boring: one request at a time, a
real browser User-Agent, a short timeout, and every failure returned as
an error string instead of an exception — a brief built from 2 of 3
competitor pages is still useful, and one dead URL must never kill the
whole run. Parsing uses html.parser, so there is nothing to install.
"""

import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser

USER_AGENT = (
    "Mozilla/5.0 (compatible; SEOContentBrief/1.0; +https://github.com/"
    "hasnaat-anjum/seo-content-brief-generator)"
)
DEFAULT_TIMEOUT = 15

# Tags whose text is page furniture, not article content.
# Note: "head" is deliberately NOT skipped — <title> lives inside it.
SKIP_TAGS = {"script", "style", "noscript", "svg"}


@dataclass
class Page:
    """One competitor page, reduced to what a brief needs."""

    url: str
    title: str = ""
    meta_description: str = ""
    headings: list = field(default_factory=list)  # [(level, text)]
    text: str = ""
    fetch_error: str = ""

    @property
    def word_count(self):
        return len(self.text.split())

    @property
    def h2s(self):
        return [text for level, text in self.headings if level == 2]

    @property
    def h3s(self):
        return [text for level, text in self.headings if level == 3]


def fetch_url(url, timeout=DEFAULT_TIMEOUT):
    """Fetch one URL. Returns (html, error); error is '' on success."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace"), ""
    except urllib.error.HTTPError as exc:
        return "", "HTTP %s" % exc.code
    except urllib.error.URLError as exc:
        return "", "could not reach host (%s)" % exc.reason
    except (TimeoutError, OSError) as exc:
        return "", "request failed (%s)" % exc


def fetch_many(urls, timeout=DEFAULT_TIMEOUT):
    """Fetch each URL in turn; returns a list of Page objects."""
    pages = []
    for url in urls:
        html, error = fetch_url(url, timeout=timeout)
        page = Page(url=url, fetch_error=error)
        if not error:
            parsed = parse_html(html, url)
            page.title = parsed.title
            page.meta_description = parsed.meta_description
            page.headings = parsed.headings
            page.text = parsed.text
        pages.append(page)
    return pages


class _PageParser(HTMLParser):
    """Pull title, meta description, headings and body text from HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta_description = ""
        self.headings = []
        self._chunks = []
        self._skip_depth = 0
        self._current_heading = None  # (level, [chunks])
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        elif tag in ("h1", "h2", "h3"):
            self._current_heading = (int(tag[1]), [])
        elif tag == "meta":
            attrs = dict(attrs)
            if attrs.get("name", "").lower() == "description":
                self.meta_description = attrs.get("content", "").strip()

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3") and self._current_heading:
            level, chunks = self._current_heading
            text = " ".join("".join(chunks).split())
            if text:
                self.headings.append((level, text))
            self._current_heading = None

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_title:
            self.title += data
        elif self._current_heading is not None:
            self._current_heading[1].append(data)
        else:
            text = data.strip()
            if text:
                self._chunks.append(text)


def parse_html(html, url=""):
    """Parse an HTML string into a Page (no network involved)."""
    parser = _PageParser()
    parser.feed(html)
    parser.close()
    # Headings also count as body text for word counts and term stats.
    heading_text = " ".join(text for _, text in parser.headings)
    body = " ".join(parser._chunks)
    full_text = " ".join(part for part in (heading_text, body) if part)
    full_text = re.sub(r"\s+", " ", full_text).strip()
    return Page(
        url=url,
        title=" ".join(parser.title.split()),
        meta_description=parser.meta_description,
        headings=parser.headings,
        text=full_text,
    )


def parse_file(path):
    """Parse a saved HTML file. Returns a Page; raises OSError if unreadable."""
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return parse_html(handle.read(), url=path)


def extract_questions(pages):
    """Question headings found on competitor pages, deduplicated.

    Only headings that actually end with a question mark count. A
    heading like "What to look for" starts with a question word but is
    a statement, not a question a reader asked.
    """
    seen = set()
    questions = []
    for page in pages:
        for _, heading in page.headings:
            text = heading.strip()
            if text.endswith("?"):
                key = text.lower()
                if key not in seen:
                    seen.add(key)
                    questions.append(text)
    return questions
