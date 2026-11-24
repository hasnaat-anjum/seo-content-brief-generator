"""Command line interface.

    python brief.py new "best budget espresso machine" \\
        --url https://example.com/guide-1 --url https://example.com/guide-2 \\
        --save --out brief.md
    python brief.py questions "best budget espresso machine"
    python brief.py titles "best budget espresso machine"
    python brief.py score examples/sample-draft.md --brief-id <id>
    python brief.py list
    python brief.py show <id>
    python brief.py export <id> --format html --out brief.html
    python brief.py delete <id>
    python brief.py niches

Every command works offline except fetching --url pages. A brief built
with no competitor pages is honest about it in its notes.
"""

import argparse
import json
import os
import sys

from .brief import Brief, build_brief, meta_options, title_options
from .intent import classify_intent
from .parse import fetch_many, parse_file
from .questions import generate_questions
from .report import (brief_to_html, brief_to_json, brief_to_markdown,
                     score_to_markdown)
from .score import score_draft
from .store import (DEFAULT_STORE, StoreError, delete_brief, get_brief,
                    list_briefs, save_brief)
from .terms import load_niches


def _load_own_pages(path):
    """Load the writer's own pages for internal-link suggestions.

    Accepts a JSON list of {"title": ..., "url": ...} objects, or a text
    file with one "Title | URL" pair per line.
    """
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return [{"title": str(item.get("title", "")),
                     "url": str(item.get("url", ""))}
                    for item in data if isinstance(item, dict)]
    except ValueError:
        pass
    pages = []
    for line in content.splitlines():
        if "|" in line:
            title, url = line.split("|", 1)
            pages.append({"title": title.strip(), "url": url.strip()})
    return pages


def _render(brief, fmt):
    if fmt == "json":
        return brief_to_json(brief)
    if fmt == "html":
        return brief_to_html(brief)
    return brief_to_markdown(brief)


def _write_or_print(text, out_path):
    if out_path:
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(text)
        print("Wrote %s" % out_path)
    else:
        print(text)


def cmd_new(args):
    pages = []
    if args.url:
        pages.extend(fetch_many(args.url))
    for path in args.file or []:
        try:
            pages.append(parse_file(path))
        except OSError as exc:
            print("Could not read %s: %s" % (path, exc), file=sys.stderr)
            return 1
    own_pages = []
    if args.pages:
        try:
            own_pages = _load_own_pages(args.pages)
        except OSError as exc:
            print("Could not read %s: %s" % (args.pages, exc),
                  file=sys.stderr)
            return 1
    if not pages:
        print("No competitor pages given — building a keyword-only brief. "
              "Add --url or --file pages for competitor data.",
              file=sys.stderr)
    brief = build_brief(args.keyword, pages, own_pages=own_pages,
                        intent_override=args.intent)
    text = _render(brief, args.format)
    if args.save:
        try:
            save_brief(brief, args.store)
            print("Saved brief %s to %s" % (brief.id, args.store),
                  file=sys.stderr)
        except StoreError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    _write_or_print(text, args.out)
    return 0


def cmd_questions(args):
    for i, question in enumerate(
            generate_questions(args.keyword, limit=args.limit), start=1):
        print("%d. %s" % (i, question))
    return 0


def cmd_titles(args):
    print("Titles (60 chars or fewer):")
    for title in title_options(args.keyword):
        print("  - %s (%d chars)" % (title, len(title)))
    print("\nMeta descriptions (160 chars or fewer):")
    for meta in meta_options(args.keyword):
        print("  - %s (%d chars)" % (meta, len(meta)))
    return 0


def cmd_score(args):
    try:
        with open(args.draft, "r", encoding="utf-8") as handle:
            draft = handle.read()
    except OSError as exc:
        print("Could not read %s: %s" % (args.draft, exc), file=sys.stderr)
        return 1
    brief_data = None
    if args.brief_id:
        try:
            brief_data = get_brief(args.brief_id, args.store)
        except StoreError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if brief_data is None:
            print("No saved brief with id '%s'. Run `brief.py list`."
                  % args.brief_id, file=sys.stderr)
            return 1
    elif args.brief_file:
        try:
            with open(args.brief_file, "r", encoding="utf-8") as handle:
                brief_data = json.load(handle)
        except (OSError, ValueError) as exc:
            print("Could not read brief %s: %s" % (args.brief_file, exc),
                  file=sys.stderr)
            return 1
    else:
        print("Score needs a brief: --brief-id <id> or --brief-file <file>.",
              file=sys.stderr)
        return 1
    brief = Brief.from_dict(brief_data)
    result = score_draft(draft, brief)
    if args.format == "md":
        print(score_to_markdown(result, brief.keyword))
        return 0
    print("Draft score for '%s': %d/100 (Grade %s)"
          % (brief.keyword, result["score"], result["grade"]))
    print("Words: %d (target %d) · Readability: Flesch %.0f — %s"
          % (result["word_count"], result["target_words"],
             result["readability"], result["readability_label"]))
    print("")
    for check in result["checks"]:
        mark = "ok " if check["points"] == check["max"] else "fix"
        print("[%s] %s — %d/%d" % (mark, check["name"],
                                   check["points"], check["max"]))
        if check["fix"]:
            print("        -> %s" % check["fix"])
    return 0


def cmd_list(args):
    try:
        briefs = list_briefs(args.store)
    except StoreError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not briefs:
        print("No saved briefs yet. Run `brief.py new \"keyword\" --save`.")
        return 0
    print("%-46s %-10s %s" % ("ID", "CREATED", "KEYWORD"))
    for brief in briefs:
        print("%-46s %-10s %s" % (brief["id"], brief.get("created", ""),
                                  brief["keyword"]))
    return 0


def cmd_show(args):
    try:
        brief_data = get_brief(args.brief_id, args.store)
    except StoreError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if brief_data is None:
        print("No saved brief with id '%s'." % args.brief_id,
              file=sys.stderr)
        return 1
    print(_render(brief_data, args.format))
    return 0


def cmd_export(args):
    try:
        brief_data = get_brief(args.brief_id, args.store)
    except StoreError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if brief_data is None:
        print("No saved brief with id '%s'." % args.brief_id,
              file=sys.stderr)
        return 1
    _write_or_print(_render(brief_data, args.format), args.out)
    return 0


def cmd_delete(args):
    try:
        deleted = delete_brief(args.brief_id, args.store)
    except StoreError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if deleted:
        print("Deleted brief %s." % args.brief_id)
    else:
        print("No saved brief with id '%s'." % args.brief_id,
              file=sys.stderr)
        return 1
    return 0


def cmd_niches(_args):
    niches = load_niches()
    if not niches:
        print("No niche packs found in data/niches.json.")
        return 0
    for niche in niches:
        print("%s" % niche["name"])
        print("  %s" % niche["note"])
        for seed in niche["seeds"]:
            print("  - %s" % seed)
        print("")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="brief.py",
        description="Build data-driven SEO content briefs from competitor "
                    "pages — free, local, no API key.")
    parser.add_argument("--store", default=DEFAULT_STORE,
                        help="brief store file (default: briefs.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="build a brief for a keyword")
    p_new.add_argument("keyword", help="target keyword, e.g. "
                       "'best budget espresso machine'")
    p_new.add_argument("--url", action="append",
                       help="competitor page URL (repeatable)")
    p_new.add_argument("--file", action="append",
                       help="saved competitor HTML file (repeatable)")
    p_new.add_argument("--pages",
                       help="your own pages for internal-link suggestions "
                            "(JSON list or 'Title | URL' lines)")
    p_new.add_argument("--intent",
                       choices=["informational", "commercial",
                                "transactional", "navigational"],
                       help="override the detected search intent")
    p_new.add_argument("--save", action="store_true",
                       help="save the brief to the store")
    p_new.add_argument("--format", choices=["md", "json", "html"],
                       default="md")
    p_new.add_argument("--out", help="write the brief to a file")
    p_new.set_defaults(func=cmd_new)

    p_q = sub.add_parser("questions", help="question keywords for a seed")
    p_q.add_argument("keyword")
    p_q.add_argument("--limit", type=int, default=10)
    p_q.set_defaults(func=cmd_questions)

    p_t = sub.add_parser("titles", help="title and meta description options")
    p_t.add_argument("keyword")
    p_t.set_defaults(func=cmd_titles)

    p_s = sub.add_parser("score", help="score a draft against a brief")
    p_s.add_argument("draft", help="draft file (Markdown or text)")
    p_s.add_argument("--brief-id", help="id of a saved brief")
    p_s.add_argument("--brief-file", help="brief JSON file")
    p_s.add_argument("--format", choices=["terminal", "md"],
                     default="terminal")
    p_s.set_defaults(func=cmd_score)

    p_l = sub.add_parser("list", help="list saved briefs")
    p_l.set_defaults(func=cmd_list)

    p_sh = sub.add_parser("show", help="show a saved brief")
    p_sh.add_argument("brief_id")
    p_sh.add_argument("--format", choices=["md", "json", "html"],
                      default="md")
    p_sh.set_defaults(func=cmd_show)

    p_e = sub.add_parser("export", help="export a saved brief to a file")
    p_e.add_argument("brief_id")
    p_e.add_argument("--format", choices=["md", "json", "html"],
                     default="md")
    p_e.add_argument("--out", required=True)
    p_e.set_defaults(func=cmd_export)

    p_d = sub.add_parser("delete", help="delete a saved brief")
    p_d.add_argument("brief_id")
    p_d.set_defaults(func=cmd_delete)

    p_n = sub.add_parser("niches", help="starter seed keywords per niche")
    p_n.set_defaults(func=cmd_niches)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except StoreError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
