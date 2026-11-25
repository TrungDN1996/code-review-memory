---
name: ingest
description: >
  Process raw source documents into wiki pages. Use when the user adds
  files to raw/ and wants them ingested, says "process this source",
  "ingest this article", "I added something to raw/", or wants to
  incorporate new material into their knowledge base.
---

# Ingest

Process raw source documents into structured, interlinked wiki pages.

## Identify Sources to Process

Determine which files need ingestion:

1. If the user specifies a file or files, use those
2. If the user says "process new sources" or similar, detect unprocessed files:
   - List all files in `raw/` (excluding `raw/assets/`)
   - Read `wiki/log.md` and extract all previously ingested source filenames from `ingest` entries
   - Any file in `raw/` not listed in the log is unprocessed
3. If no unprocessed files are found, tell the user

## Extract Non-Markdown Sources with markitdown

Before reading a source, check if it needs extraction:

**Check markitdown availability:**
```bash
markitdown --version
```
If that fails, markitdown is not installed — skip extraction and proceed with direct reading.

**File types that benefit from markitdown extraction:**
PDF, DOCX, PPTX, XLSX, XLS, images (JPG/PNG), audio (WAV/MP3), EPUB, HTML, ZIP, YouTube URLs, CSV, JSON, XML

**If markitdown is available and the file is one of those types:**
1. Run extraction to a temp markdown file:
   ```bash
   markitdown "raw/path/to/file.pdf" -o "raw/path/to/file.extracted.md"
   ```
2. Read the extracted `.extracted.md` file instead of the original
3. Delete the temp file after ingestion is complete

## Process Each Source

For each source file, follow this workflow:

### 1. Read the source completely

Read the entire file (or its extracted markdown if markitdown was used). If the file contains image references, note them — read the images separately if they contain important information.

### 2. Discuss key takeaways with the user

Before writing anything, share the 3-5 most important takeaways from the source. Ask the user if they want to emphasize any particular aspects or skip any topics. Wait for confirmation before proceeding.

### 3. Create source summary page

Create a new file in `wiki/sources/` named after the source (slugified). Include:

    ---
    title: Page Title
    type: concept | entity | source-summary | synthesis
    sources:
      - raw/papers/filename.md
    related:
      - "[[related-concept]]"
    created: YYYY-MM-DD
    updated: YYYY-MM-DD
    confidence: high | medium | low
    ---

    # Source Title

    **Source:** original-filename.md
    **Date ingested:** YYYY-MM-DD
    **Type:** article | paper | transcript | notes | etc.

    ## Summary

    Structured summary of the source content.

    ## Key Claims

    - Claim 1
    - Claim 2
    - ...

    ## Entities Mentioned

    - [[Entity Name]] — brief context
    - ...

    ## Concepts Covered

    - [[Concept Name]] — brief context
    - ...

### 4. Update entity and concept pages

For each entity (person, organization, product, tool) and concept (idea, framework, theory, pattern) mentioned in the source:

**If a wiki page already exists:**
- Read the existing page
- Add new information from this source
- Add the source to the `sources:` frontmatter list
- Update the `updated:` date
- Note any contradictions with existing content, citing both sources

**If no wiki page exists:**
- Create a new page in the appropriate subdirectory:
  - `wiki/entities/` for people, organizations, products, tools
  - `wiki/concepts/` for ideas, frameworks, theories, patterns
- Include YAML frontmatter with tags, sources, created, and updated fields
- Write a focused summary based on what this source says about the topic

**Structure of wiki/concepts/:**
```
wiki/concepts/
├── standards/
│   ├── backend/         — backend rules (API design, error-handling, DI, patterns)
│   ├── ui/              — UI rules (components, accessibility, styling)
│   ├── unit-test/       — unit test rules (structure, mocking, assertions)
│   ├── spec-test/       — spec/integration test rules (BDD, e2e, contract testing)
│   ├── sql/             — SQL rules (queries, schema design, performance)
│   └── general/         — cross-cutting rules (clean-code, naming, code-document)
└── knowledge-sharing/   — domain models, processes, and institutional knowledge
```

When creating a concept page, pick the most specific slot:
- Backend rule → `standards/backend/`
- UI rule → `standards/ui/`
- Unit test rule → `standards/unit-test/`
- Spec/integration/e2e/BDD test rule → `standards/spec-test/`
- SQL rule → `standards/sql/`
- Cross-cutting rule → `standards/general/`
- Domain/process knowledge → `knowledge-sharing/`
- Each page's metadata has the specific tags

### 5. Add wikilinks

Ensure all related pages link to each other using `[[wikilink]]` syntax. Every mention of an entity or concept that has its own page should be linked.

### 6. Update wiki/index.md

For each new page created, add an entry under the appropriate category header:

    - [[page-name]] — one-line summary (under 120 characters)

### 7. Update wiki/log.md

Append:

    ## [YYYY-MM-DD] ingest | Source Title
    Processed source-filename.md. Created N new pages, updated M existing pages.
    New entities: [[entity-name1]], [[entity-name2]]. New concepts: [[concept-name1]].

### 8. Report results

Tell the user what was done:
- Pages created (with links)
- Pages updated (with what changed)
- New entities and concepts identified
- Any contradictions found with existing content

## Conventions

- Source summary pages are **factual only**. Save interpretation and synthesis for concept and synthesis pages.
- A single source typically touches **10-15 wiki pages**. This is normal and expected.
- When new information contradicts existing wiki content, **update the wiki page and note the contradiction** with both sources cited.
- **Prefer updating existing pages** over creating new ones. Only create a new page when the topic is distinct enough to warrant its own page.
- Use `[[wikilinks]]` for all internal references. Never use raw file paths.

## What's Next

After ingesting sources, the user can:
- **Ask questions** with `/query` to explore what was ingested
- **Ingest more sources** — clip another article and run `/ingest` again
- **Health-check** with `/lint` after every 10 ingests to catch gaps