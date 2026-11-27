# LLM Wiki

A personal knowledge base maintained by Claude Code.
Based on [Andrej Karpathy's LLM Wiki pattern](llm-wiki.md).

## Project Structure

```
├── raw/                    # Immutable source documents
│
├── wiki/                   # LLM-generated and maintained markdown pages
│   ├── index.md            # Master content catalog. Update on every operation
│   ├── log.md              # Append-only operation log. Entries: ## [YYYY-MM-DD] type | Title
│   ├── sources/            # One page per ingested source
│   ├── entities/           # People, orgs, tools, frameworks
│   ├── concepts/           # Ideas, patterns, techniques. One axis per level — the directory is what the rule constrains
│   │   ├── standards/      # Rules on code
│   │   │   ├── csharp/     # C#-only rules
│   │   │   ├── typescript/ # TypeScript-only rules
│   │   │   ├── sql/        # SQL rules
│   │   │   ├── ui/         # User-facing behavior, any language
│   │   │   ├── testing/    # unit/ and spec/
│   │   │   │   ├── unit/   # Backend test rules (C#/SQL)
│   │   │   │   └── spec/   # UI test rules
│   │   │   └── cross-cutting/ # Language-independent code rules
│   │   ├── practices/      # Rules on how work happens (process, coordination)
│   │   ├── knowledge-sharing/ # Domain and product facts, no rules
│   │   └── others/         # Nothing above fits
│   └── synthesis/          # comparisons, analyses, cross-cutting themes
├── output/                 # Reports, query results, and generated artifacts go here
```

## Index Format

Each entry in `wiki/index.md` is one line:

    - [[page-name]] — one-line summary

Organized under category headers: Sources, Entities, Concepts, Synthesis.

## Log Format

Each entry in `wiki/log.md`:

    ## [YYYY-MM-DD] operation | Title
    Brief description of what was done.

Operations: `ingest`, `lint`, `prune` (delete a page), `move` (change directory), `rename` (change slug), `rewrite` (substantially change a page's content).

## Page Naming

Filenames use **kebab-case** with `.md` extension. Page titles inside the file use **Title Case**.

- Source pages: `wiki/sources/article-title-here.md` → `# Article Title Here`
- Entity pages: `wiki/entities/entity-name.md` → `# Entity Name`
- Concept pages: `wiki/concepts/<category>/concept-name.md` → `# Concept Name` (category = `standards/{csharp,typescript,sql,ui,testing/unit,testing/spec,cross-cutting}`, `practices`, `knowledge-sharing`, or `others`)
- Synthesis pages: `wiki/synthesis/comparison-topic.md` → `# Comparison Topic`

When creating `[[wikilinks]]`, use the filename (kebab-case), not the page title (Title Case):
- Correct: `[[entity-name]]`
- Wrong: `[[Entity Name]]`

To slugify a title into a filename: lowercase, replace spaces with hyphens, remove special characters, trim to reasonable length.

## Lint Frequency

Run a lint pass (`/lint`) on this schedule:
- **After every 10 ingests** — catches cross-reference gaps while they're fresh
- **Monthly at minimum** — catches stale claims and orphan pages that accumulate over time
- **Before any major query or synthesis** — ensures the wiki is healthy before you rely on it for analysis

## Rules

1. Never modify files in `raw/`. They are immutable source material.
2. Always update `wiki/index.md` when you create or delete a page.
3. Always append to `wiki/log.md` when you perform an operation.
4. Use `[[wikilinks]]` for all internal references.
5. Every wiki page must have YAML frontmatter with tags, sources, created, and updated fields.
6. When new information contradicts existing wiki content, update the wiki page and note the contradiction with both sources cited.
7. Keep source summary pages factual. Save interpretation and synthesis for concept and synthesis pages.
8. When asked a question, search the wiki first. Only go to raw sources if the wiki doesn't have the answer.
9. Prefer updating existing pages over creating new ones. Only create a new page when the topic is distinct enough to warrant it.
10. Keep `wiki/index.md` concise — one line per page, under 120 characters per entry.
11. Before deleting, moving, or renaming a page, grep `wiki/` for inbound `[[slug]]` links. Delete or repoint every one (except old `log.md` entries), update `index.md`, remove directories left empty, and log the operation. After the change, grep again to confirm no stale links remain.