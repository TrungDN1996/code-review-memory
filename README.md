# Code Review Memory

An LLM-maintained code review knowledge base built on the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Drop raw sources into a folder, let the LLM compile them into a structured wiki, and browse it all in Obsidian.

## How It Works

You feed raw material (articles, papers, notes, transcripts) into a `raw/` folder. The LLM reads everything, writes structured wiki pages, creates cross-references, and maintains an index. You browse the results in Obsidian — following links, exploring the graph view, and asking questions.

The LLM is the librarian. You're the curator.

## Prerequisites

- **[Obsidian](https://obsidian.md)** — the markdown editor you'll browse your wiki in
- **An AI coding agent** — [Claude Code](https://claude.ai/code), [Codex](https://openai.com/codex)

## Quick Start

1. **Open in Obsidian** — launch Obsidian, choose "Open folder as vault", select your vault folder
2. **Pull GitLab comments** into `raw/` (see [Pulling from GitLab](#pulling-from-gitlab) below)
3. **Run the skill** — agent follows its steps automatically

| Step | Slash command | What it does |
|---|---|---|
| Ingest a source | `/ingest` | Reads `raw/`, writes wiki pages, updates index |
| Ask a question | `/query` | Searches wiki, answers from structured pages |
| Health-check | `/lint` | Finds broken links, orphan pages, stale claims |

**Browse results** in Obsidian — follow `[[wikilinks]]`, explore graph view, check `wiki/index.md`

## Pulling from GitLab

`tools/gitlab.py` fetches merged MR comments from GitLab and writes export files to `raw/`.

**1. Configure `.env`** in the `tools/` folder:

```env
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=your_personal_access_token
GITLAB_PROJECT_ID=123
```

**2. Run:**

```sh
cd tools
uv run gitlab.py
```

Prompts for how many MRs to fetch — press Enter for all, or type a number (e.g. `50` for the 50 most recent merged MRs).

Output: one or more JSON files in `raw/`, named by date range. Run `/ingest` after to process them into wiki pages.

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