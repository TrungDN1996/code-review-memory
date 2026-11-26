---
name: lint
description: >
  Health-check the wiki for contradictions, orphan pages, stale claims,
  and missing cross-references. Use when the user says "audit",
  "health check", "lint", "find problems", or wants to improve wiki quality.
---

# Lint

Health-check the wiki and report issues with actionable fixes.

## Audit Steps

Run all checks below, then present a consolidated report.

### 1. Broken wikilinks

Scan all wiki pages for `[[wikilink]]` references. For each link, verify the target page exists. Report any broken links.

```bash
# Find all wikilinks across wiki pages
grep -roh '\[\[[^]]*\]\]' wiki/ | sort -u
```

Cross-reference against actual files in `wiki/`.

### 2. Orphan pages

Find pages with no inbound links — no other page references them via `[[wikilink]]`.

For each `.md` file in `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/synthesis/`:
- Extract the page name (filename without extension)
- Search all other wiki pages for `[[page-name]]`
- If no other page links to it, it's an orphan

### 3. Contradictions

Read pages that share entities or concepts and look for conflicting claims. Flag when:
- Two source summaries make opposing claims about the same topic
- An entity page contains information that conflicts with a source summary
- A concept/standard page conflicts with another concept/standard page (e.g. two rules in the same category give opposite guidance)
- Dates, figures, or factual claims differ between pages

For each contradiction, cite both pages (file + line) and both sources — when fixing, update the page and note the contradiction with both sources cited. Group pages by shared `[[wikilinks]]` and shared tags first, then diff their claims — don't rely on topic name alone.

### 4. Stale claims

Cross-reference source dates with wiki content. Flag when:
- A concept page cites only old sources and newer sources exist on the same topic
- Entity information hasn't been updated despite newer sources mentioning that entity

### 5. Missing pages

Scan for `[[wikilinks]]` that point to pages that don't exist yet. These are topics the wiki mentions but hasn't given their own page. Assess whether they warrant a page.

### 6. Missing cross-references

Find pages that discuss the same topics but don't link to each other. Look for:
- Entity pages that mention concepts without linking them
- Concept pages that mention entities without linking them
- Source summaries that cover the same topic but don't reference each other

### 7. Index consistency

Verify `wiki/index.md` is complete and accurate:
- Every page in `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/synthesis/` has an index entry
- No index entries point to deleted pages
- Entries are under the correct category header

### 8. Data gaps

Based on the wiki's current coverage, suggest:
- Topics mentioned frequently but lacking depth
- Questions the wiki can't answer well
- Areas where a web search could fill in missing information

### 9. Lost content

`wiki/` is gitignored, so git history is not available — use `wiki/log.md` and `raw/` as the source of truth instead. Find content that used to exist but is now gone or weaker, not just never written. Flag when:
- `wiki/log.md` records an ingest or update describing a claim/page, but that page no longer exists, or no longer contains the claim the log entry describes
- `wiki/index.md` references a page (or a `[[wikilink]]` elsewhere does) that no log.md entry ever created and that doesn't exist — may have been deleted without an update
- A page's `updated` frontmatter date is older than its newest `sources` entry's ingest date, with no log.md entry explaining the gap
- A `raw/` source contains facts that a log.md entry says were ingested, but those facts aren't found in any current wiki page (re-read the relevant `raw/` file and diff against the page `sources` point to)

### 10. Duplication

Find pages (or sections) that cover the same ground. Per rule 9, prefer merging into the existing page over keeping both. Flag when:

- Two pages state the same rule or fact with different wording — same category, or one in `standards/<language>/` and one in `standards/cross-cutting/`
- A concept page restates a source summary instead of interpreting it (rule 7)
- Two source pages summarize the same underlying source (same URL, title, or `raw/` file)
- An entity's details are spelled out in full on several pages rather than linked via `[[wikilink]]`
- Two pages differ only by slug (`unit-testing` vs `unit-tests`, singular vs plural, abbreviation vs full word)

Group by shared tags and shared `[[wikilinks]]` first, then compare claims — slug similarity alone is a weak signal. Fix by keeping the page with the richer history and more inbound links, merging the unique claims into it, replacing the other with nothing (delete it), and repointing every inbound `[[wikilink]]`, plus `wiki/index.md`.

### 11. Misplaced content

Verify each page sits in the directory its content calls for — one axis per level, per the routing rules in `/ingest`. Flag when:

- A rule on code sits in `practices/`, or a process rule sits in `standards/`
- A page with no rule at all (pure domain or product fact) sits under `standards/` or `practices/` instead of `knowledge-sharing/`
- A language-specific rule sits in `standards/cross-cutting/`, or a language-independent rule sits in `standards/csharp|typescript|sql/`
- A test rule sits outside `standards/testing/unit|spec/`, or a user-facing-behavior rule sits outside `standards/ui/`
- A page sits in `others/` though one of the categories above now fits
- Interpretation or synthesis lives on a `sources/` page (rule 7), or a page mixes two axes and should be split
- A page is tagged with its own path segment (e.g. `standards` tag inside `standards/`)

Fix by moving the file, updating `wiki/index.md` (entry and category header), and repointing inbound `[[wikilinks]]` if the slug changes. Log the move.

## Report Format

Present findings grouped by severity:

### Errors (must fix)
- Broken wikilinks
- Contradictions between pages
- Index entries pointing to missing pages
- Lost content: claims/sections dropped from a page with no log entry
- Duplicate pages making conflicting versions of the same claim

### Warnings (should fix)
- Orphan pages with no inbound links
- Stale claims from outdated sources
- Missing pages for frequently referenced topics
- Duplicate pages or sections covering the same ground
- Misplaced pages: wrong category directory for their content

### Info (nice to fix)
- Potential cross-references to add
- Data gaps that could be filled
- Index entries that could be more descriptive

For each finding, include:
- **What:** description of the issue
- **Where:** the specific file(s) and line(s)
- **Fix:** what to do about it

## After the Report

Ask the user:
> "Found N errors, N warnings, and N info items. Want me to fix any of these?"

If the user agrees, fix issues and report what changed.

## Log the lint pass

Append to `wiki/log.md`:

    ## [YYYY-MM-DD] lint | Health check
    Found N errors, N warnings, N info items. Fixed: [list of fixes applied].

## When to Lint

- **After every 10 ingests** — catches cross-reference gaps while they're fresh
- **Monthly at minimum** — catches stale claims and orphan pages over time
- **Before major queries** — ensures the wiki is healthy before you rely on it for analysis

## Related Skills

- `/ingest` — process new sources into wiki pages
- `/query` — ask questions against the wiki