# Code Review Memory

An LLM-maintained code review knowledge base built on the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Drop raw sources into a folder, let the LLM compile them into a structured wiki, and browse it all in Obsidian.

## How It Works

You feed raw material (articles, papers, notes, transcripts) into a `raw/` folder. The LLM reads everything, writes structured wiki pages, creates cross-references, and maintains an index. You browse the results in Obsidian — following links, exploring the graph view, and asking questions.

The LLM is the librarian. You're the curator.

## Prerequisites

- **[Obsidian](https://obsidian.md)** — the markdown editor you'll browse your wiki in
- **An AI coding agent** — [Claude Code](https://claude.ai/code), [Codex](https://openai.com/codex)

## Quick Start

- **Open in Obsidian** — launch Obsidian, choose "Open folder as vault", select your vault folder
- **Clip your first article** to `raw/`, then run `/ingest` — the LLM will discuss key takeaways and build wiki pages
- **Browse your wiki** in Obsidian — follow `[[wikilinks]]`, explore the graph view, check `wiki/index.md`
- **Keep going** — `/query` to ask questions, `/lint` to health-check

## What You Get

```
your-vault/
├── raw/                    # Your inbox — drop sources here
│   └── assets/             # Images and attachments
├── wiki/                   # LLM-maintained wiki
│   ├── sources/            # One summary per ingested source
│   ├── entities/           # People, orgs, products, tools
│   ├── concepts/           # Ideas, frameworks, theories
│   ├── synthesis/          # Comparisons, analyses, themes
│   ├── index.md            # Master catalog of all pages
│   └── log.md              # Chronological operation record
├── output/                 # Reports and generated artifacts
└── CLAUDE.md               # Agent config (varies by agent)
```

## Optional Tools

The wizard offers to install these. All optional but recommended:

- **[markitdown](https://github.com/microsoft/markitdown)** — convert non-markdown files to markdown before ingestion
- **[summarize](https://github.com/steipete/summarize)** — summarize links, files, and media from the CLI
- **[qmd](https://github.com/tobi/qmd)** — local search engine for markdown files (useful as wiki grows)

## Based On

- [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)