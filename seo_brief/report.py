"""Render a brief (or a draft score) as Markdown, JSON or HTML.

The Markdown brief is the deliverable: a writer can paste it into
Notion, Google Docs or a GitHub issue and start writing. The HTML
version is self-contained (inline CSS, no JavaScript, no external
requests) so it can be emailed to a client as one file.
"""

import html
import json

_CSS = """
body { font-family: Georgia, 'Times New Roman', serif; max-width: 760px;
  margin: 2rem auto; padding: 0 1.2rem; color: #1f2937; line-height: 1.6; }
h1 { font-size: 1.7rem; border-bottom: 3px solid #0f766e; padding-bottom: .4rem; }
h2 { font-size: 1.25rem; color: #0f766e; margin-top: 1.8rem; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th, td { border: 1px solid #d1d5db; padding: .45rem .6rem; text-align: left;
  font-size: .92rem; }
th { background: #f0fdfa; }
code { background: #f3f4f6; padding: .1rem .3rem; border-radius: 3px; }
.meta { color: #6b7280; font-size: .9rem; }
.tag { display: inline-block; background: #ccfbf1; color: #115e59;
  border-radius: 999px; padding: .1rem .6rem; font-size: .8rem;
  margin-right: .3rem; }
"""


def brief_to_markdown(brief):
    """Render a Brief (or brief dict) as Markdown."""
    b = brief if isinstance(brief, dict) else brief.to_dict()
    lines = []
    lines.append("# Content Brief: %s" % b["keyword"])
    lines.append("")
    lines.append("**Content type:** %s · **Intent:** %s (%s) · "
                 "**Target length:** %d words (competitors: %d–%d words)"
                 % (b["content_type"], b["intent"], b["intent_signal"],
                    b["target_words"], b["word_range"]["min"],
                    b["word_range"]["max"]))
    if b.get("local"):
        lines.append("**Local:** yes — include service area, opening hours "
                     "and reviews.")
    lines.append("")
    if b.get("notes"):
        lines.append("> **Notes:** " + " ".join(b["notes"]))
        lines.append("")
    lines.append("## Suggested titles")
    lines.append("")
    for title in b["titles"]:
        lines.append("- %s" % title)
    lines.append("")
    lines.append("## Suggested meta descriptions")
    lines.append("")
    for meta in b["meta_descriptions"]:
        lines.append("- %s" % meta)
    lines.append("")
    lines.append("## Outline (%d words total)" % b["target_words"])
    lines.append("")
    for section in b["outline"]:
        lines.append("- **%s** (~%d words, covered by %d of %d competitors)"
                     % (section["title"], section["words"],
                        section["coverage"], len(b["competitor_table"])))
        for sub in section.get("subheadings", []):
            lines.append("  - %s" % sub)
    lines.append("")
    lines.append("## Must-include terms")
    lines.append("")
    lines.append("Terms competitors use that this article should cover too:")
    lines.append("")
    for term in b["must_include_terms"]:
        lines.append("- `%s` — on %d competitor page(s), %d mentions"
                     % (term["term"], term["pages"], term["count"]))
    lines.append("")
    lines.append("## Questions to answer")
    lines.append("")
    for question in b["questions"]:
        lines.append("- %s" % question)
    lines.append("")
    lines.append("## Competitors analysed")
    lines.append("")
    lines.append("| Page | Words | Headings | Score /30 |")
    lines.append("|---|---|---|---|")
    for row in b["competitor_table"]:
        lines.append("| [%s](%s) | %d | %d | %d |"
                     % (row["title"], row["url"], row["words"],
                        row["headings"], row["score"]))
    lines.append("")
    if b["gaps"]:
        lines.append("## Gaps to win")
        lines.append("")
        for gap in b["gaps"]:
            lines.append("- %s" % gap)
        lines.append("")
    if b["internal_links"]:
        lines.append("## Internal links to add")
        lines.append("")
        for link in b["internal_links"]:
            lines.append("- [%s](%s) — matches: %s"
                         % (link["title"], link["url"],
                            ", ".join(link["matched_words"])))
        lines.append("")
    lines.append("## E-E-A-T checklist")
    lines.append("")
    for item in b["eeat_checklist"]:
        lines.append("- [ ] %s" % item)
    lines.append("")
    lines.append("## Call to action")
    lines.append("")
    lines.append(b["call_to_action"])
    lines.append("")
    lines.append("---")
    lines.append("*Brief %s · created %s · Built with "
                 "seo-content-brief-generator — numbers are measured from "
                 "the competitor pages above, not from search-volume data.*"
                 % (b["id"], b["created"]))
    lines.append("")
    return "\n".join(lines)


def brief_to_html(brief):
    """Render a Brief as a self-contained HTML page."""
    b = brief if isinstance(brief, dict) else brief.to_dict()
    markdown = brief_to_markdown(b)
    body = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            body.append("<h1>%s</h1>" % html.escape(line[2:]))
        elif line.startswith("## "):
            body.append("<h2>%s</h2>" % html.escape(line[3:]))
        elif line.startswith("- "):
            body.append("<li>%s</li>" % html.escape(line[2:]))
        elif line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            tag = "th" if set(cells[0]) <= set("-: ") else "td"
            if set("".join(cells)) <= set("-: |"):
                continue
            body.append("<tr>%s</tr>" % "".join(
                "<%s>%s</%s>" % (tag, html.escape(c), tag) for c in cells))
        elif line.strip():
            body.append("<p>%s</p>" % html.escape(line))
    table_html = "".join(body)
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<title>Content Brief: %s</title>\n<style>%s</style>\n</head>\n"
            "<body>\n%s\n</body>\n</html>"
            % (html.escape(b["keyword"]), _CSS, table_html))


def brief_to_json(brief):
    """Render a Brief as indented JSON."""
    b = brief if isinstance(brief, dict) else brief.to_dict()
    return json.dumps(b, indent=2, ensure_ascii=False) + "\n"


def score_to_markdown(result, keyword):
    """Render a draft-score dict as Markdown."""
    lines = []
    lines.append("# Draft Score: %s" % keyword)
    lines.append("")
    lines.append("**Score: %d/100 (Grade %s)** · %d words (target %d) · "
                 "Readability: Flesch %.0f — %s"
                 % (result["score"], result["grade"], result["word_count"],
                    result["target_words"], result["readability"],
                    result["readability_label"]))
    lines.append("")
    lines.append("| Check | Points |")
    lines.append("|---|---|")
    for check in result["checks"]:
        lines.append("| %s | %d/%d |" % (check["name"], check["points"],
                                         check["max"]))
    lines.append("")
    if result["fixes"]:
        lines.append("## Fixes, in order of impact")
        lines.append("")
        for fix in result["fixes"]:
            lines.append("- %s" % fix)
        lines.append("")
    else:
        lines.append("No fixes needed — this draft follows the brief.")
        lines.append("")
    return "\n".join(lines)
