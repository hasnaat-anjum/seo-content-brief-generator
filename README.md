# SEO Content Brief Generator

**Turn a keyword and your competitors' pages into a writer's brief — in seconds, on your own machine, with no account and no API key.**

A content brief is the document a writer opens before writing: what the page is for, how long it should be, what it must cover, what to call it, and how to make it trustworthy. Good briefs come from reading the pages that already rank. This tool does that reading for you — it fetches (or loads) competitor pages, merges their headings into one outline, finds the terms they all use, lists the questions they answer, and scores your draft against the brief when it's written.

## The problem it fills

Every content team writes SEO briefs, but the tools that build them from real competitor pages cost $50–170/month (Surfer, Frase, Clearscope), and the free options are either blank templates or skills that only run inside an AI coding agent. There is no standalone, no-signup, no-API-key tool a freelancer can just run. This is that tool: free, local, standard library only, and honest about what it knows — every number in a brief is measured from the competitor pages you give it, never invented search volume.

## Features

- **Data-driven briefs** — from competitor URLs (`--url`) or saved HTML files (`--file`), so it works fully offline on pages you already have.
- **Search intent + content type** — classifies the keyword (informational / commercial / transactional / navigational, plus local) and recommends the page format: how-to guide, buying guide, listicle, comparison page or product page.
- **Merged outline** — competitor H2/H3 headings are deduplicated ("What to look for" / "How to choose" / "What actually matters" become one section), listicle items are grouped under one "Top picks" section, and the target word count is split across sections by how many competitors cover them.
- **Target length from real pages** — the brief's word target is the median competitor length, with the min–max range shown.
- **Must-include terms** — the words and phrases competitors all use, ranked by coverage (stopwords, the seed keyword itself and generic filler are filtered out).
- **Questions to answer** — question headings competitors use, plus generated question keywords for the seed ("How to choose…?", "What is the best…?"), with verb-phrase seeds ("how to start a food blog") handled properly.
- **Titles + meta descriptions** — five title options (60 chars or fewer) and three meta descriptions (160 chars or fewer), built from the seed without doubled words.
- **Gaps to win** — sections few competitors cover and questions none of them answer, capped at five.
- **E-E-A-T checklist + CTA** — trust signals tailored to the page format, and a call to action matched to the intent.
- **Internal-link suggestions** — give it your own pages (`--pages`) and it suggests which to link, ranked by topic overlap.
- **Draft scoring** — `score` grades a draft 0–100 (A–F) against its brief: keyword placement, outline coverage, length vs target, readability (Flesch), and must-include terms, with a concrete fix for every point lost.
- **Saved briefs** — briefs are kept in one JSON store (`briefs.json`), written atomically with a `.bak` backup. List, show, export (Markdown / JSON / HTML) and delete them.
- **Niche starter packs** — `niches` lists seed keywords for ecommerce, local services, SaaS, blogging, freelancing and food blogs.

## Quick start

Requires Python 3.9+ — no packages to install.

```bash
# 1. Build a brief from the three example competitor pages
python brief.py new "best budget espresso machine for beginners" \
  --file examples/competitors/budget-espresso-guide.html \
  --file examples/competitors/cheap-espresso-list.html \
  --file examples/competitors/budget-espresso-buying-guide.html \
  --save --out brief.md

# 2. Score the sample draft against that brief
python brief.py score examples/sample-draft.md \
  --brief-id best-budget-espresso-machine-for-beginners-20261124

# 3. Just the questions, or just title ideas
python brief.py questions "best budget espresso machine for beginners"
python brief.py titles "best budget espresso machine for beginners"
```

With live competitor pages instead of files:

```bash
python brief.py new "best budget espresso machine for beginners" \
  --url https://example.com/guide-1 \
  --url https://example.com/guide-2 \
  --pages my-pages.json --save
```

`my-pages.json` is a list of `{"title": ..., "url": ...}` objects (or a text file with one `Title | URL` pair per line) used for internal-link suggestions.

## What a brief contains

The example brief in `examples/sample-brief.md` was built from the three example competitor pages. For "best budget espresso machine for beginners" it finds commercial intent, a listicle format, a 600-word target (competitors: 582–681 words), a 7-section outline (the "how to choose" sections from all three pages merged into one), 15 must-include terms (`grinder`, `milk`, `coffee`, `steam wand`…), 10 questions to answer, and 3 gaps to win — plus titles, meta descriptions, an E-E-A-T checklist and a CTA.

The sample draft in `examples/sample-draft.md` scores **76/100 (Grade C)** against it (`examples/sample-draft-score.md`): it covers 4 of 7 sections, runs 314 of 600 target words, and misses the term "coffee" — each with a concrete fix.

## Commands

| Command | What it does |
|---|---|
| `new KEYWORD [--url …] [--file …] [--pages …] [--intent …] [--save] [--format md\|json\|html] [--out FILE]` | Build a brief |
| `questions KEYWORD [--limit N]` | Question keywords for a seed |
| `titles KEYWORD` | Title and meta description options |
| `score DRAFT --brief-id ID \| --brief-file FILE [--format terminal\|md]` | Score a draft against a brief |
| `list` | List saved briefs |
| `show ID [--format md\|json\|html]` | Show a saved brief |
| `export ID --format md\|json\|html --out FILE` | Export a saved brief |
| `delete ID` | Delete a saved brief |
| `niches` | Starter seed keywords per niche |

Use `--store PATH` (before the subcommand) to keep briefs somewhere other than `briefs.json` in the current folder.

## Honest limits

- **No search volume, no keyword difficulty from real data.** No free source can provide accurate monthly volumes, so this tool does not invent them. The brief tells you what to write about and how long to write it, not how many people search for it — pair it with a volume source (e.g. Google Keyword Planner) when you need exact numbers.
- **Fetching is polite and single-threaded.** A competitor page that blocks the request is reported in the brief's notes and left out; a brief from 2 of 3 pages is still useful.
- **Intent and content type are heuristics** from the words in the keyword. Override with `--intent` when you know better.

## Tests

111 tests, standard library `unittest` only:

```bash
python -m unittest discover -s tests -v
```

## Project layout

```
brief.py                  Entry point
seo_brief/
  cli.py                  Subcommands (new, questions, titles, score, ...)
  intent.py               Search-intent classification + content type
  parse.py                Polite fetching + HTML parsing (html.parser)
  terms.py                Must-include term extraction (TF-IDF style)
  questions.py            Question-keyword templates
  outline.py              Competitor heading merger + word allocation
  brief.py                Brief assembly (titles, metas, gaps, E-E-A-T, CTA)
  score.py                Draft scoring + Flesch readability
  store.py                Atomic JSON brief store with .bak backup
  report.py               Markdown / JSON / HTML renderers
data/
  stopwords.txt           Stopwords for the term extractor
  niches.json             Starter seed keywords per niche
examples/
  competitors/            Three example competitor pages (HTML)
  sample-brief.md         Brief built from those pages
  sample-draft.md         A deliberately incomplete draft
  sample-draft-score.md   Its score report (76/100, Grade C)
tests/                    111 tests, one file per module
```

## Who it helps

Freelance SEO writers and content marketers who write briefs by hand today; small-business owners writing their own blog posts and product guides; and anyone who wants a repeatable, explainable brief instead of a $100/month subscription — with nothing uploaded anywhere.

## License

MIT — see `LICENSE`.
