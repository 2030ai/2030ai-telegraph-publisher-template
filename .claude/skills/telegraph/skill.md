---
name: telegraph
description: "Publish Claude artifacts to telegra.ph — HTML, Markdown, plain text. Instant shareable link."
triggers:
  - "telegraph"
  - "телеграф"
  - "telegra.ph"
  - "опубликуй"
  - "publish"
---

# Telegraph Publisher

Script: `~/.claude/telegraph/publish.py` (stdlib only, zero dependencies).

## Commands

| Command  | Description |
|----------|-------------|
| `create` | Create page. `--title` (required), `--format`, `--file` or stdin, `--author-name`, `--author-url` |
| `edit`   | Edit page. `--path`, `--title`, `--format`, `--file` or stdin, `--author-name`, `--author-url` |
| `get`    | Page info. `--path`, `--return-content` |
| `list`   | List created pages. `--offset`, `--limit` |
| `upload` | Upload image. `--file` → returns Telegraph URL for embedding |

## Format detection

Format is auto-detected from `--file` extension:
- `.md` / `.markdown` → markdown
- `.html` / `.htm` → html
- `.txt` → text

Override with `--format`. Default for stdin without `--format`: html.

## Choosing the right format

- **Markdown** — best default for most generated content: articles, notes, reports, summaries
- **HTML** — when you need precise control or are converting existing HTML
- **Text** — for plain text without any formatting

When generating content for Telegraph, prefer Markdown — it's more readable in source form and the converter handles all Telegraph-specific mapping.

## Workflow

When user asks to "publish to telegraph", "share as a link", or "опубликуй":
1. Generate content as Markdown (preferred) or HTML
2. Write to a temp file or pipe via heredoc
3. Call the script, capture JSON output
4. Return the URL to the user

### Heredoc — Markdown (preferred)

```bash
python3 ~/.claude/telegraph/publish.py create --title "My Article" --format markdown <<'CONTENT'
# Introduction

This is the article body with **bold** and *italic* text.

- List item one
- List item two

> A blockquote for emphasis

| Name  | Role     |
|-------|----------|
| Alice | Engineer |
| Bob   | Designer |
CONTENT
```

### Heredoc — HTML

```bash
python3 ~/.claude/telegraph/publish.py create --title "My Page" <<'CONTENT'
<h3>Section</h3>
<p>Paragraph with <b>bold</b> text.</p>
<ul>
<li>Item one</li>
<li>Item two</li>
</ul>
CONTENT
```

### File-based

```bash
python3 ~/.claude/telegraph/publish.py create --title "Report" --file /tmp/report.md
```

### Image upload + embed

```bash
# 1. Upload image
python3 ~/.claude/telegraph/publish.py upload --file screenshot.png
# → {"ok": true, "url": "https://telegra.ph/file/abc123.png"}

# 2. Use returned URL in content
python3 ~/.claude/telegraph/publish.py create --title "With Image" --format markdown <<'CONTENT'
# Screenshot

![Screenshot](https://telegra.ph/file/abc123.png)
CONTENT
```

## Typography guidelines

Telegraph pages should feel like a well-designed article, not a raw dump. Key principles:

### Structure and rhythm

- **Don't repeat the title** in content. Telegraph shows `--title` as a large h1 automatically. Starting content with `# Same Title` creates an ugly duplicate.
- **Use h3 sparingly** — only for major sections (2-4 per page). For subsections, use **bold text** at the start of a paragraph instead of h4.
- **Add `---` (horizontal rules)** between major sections to create visual breathing room.
- **Start with a lead paragraph** — 1-2 sentences that hook the reader. No heading before it.

### Visual variety

- **Alternate block types** — don't stack 5 bullet lists in a row. Mix paragraphs, lists, blockquotes, code blocks, tables.
- **Use `>` blockquotes** for key takeaways, important notes, or TL;DR summaries. They stand out visually.
- **Bold key terms** in running text to create scan points. But don't bold entire sentences.
- **Short paragraphs** — 2-3 sentences max. One idea per paragraph.

### Tables

- Tables render as monospace `<pre>` with box-drawing borders — they look clean, use freely.
- **Escape `|` in cell content** — a literal `|` inside a cell breaks column parsing. Avoid pipes in table data.
- Keep tables compact: short column headers, concise values.

### What NOT to do

- Don't create walls of same-level headings (h3, h3, h3, h3, h3...)
- Don't put every detail in bullet points — use prose for context, lists for enumerations
- Don't use `<code>` for regular words that aren't code
- Don't generate content that looks like a README — Telegraph is for readable articles

## Output

JSON on stdout: `{"ok": true, "url": "https://telegra.ph/...", "path": "..."}`

Multi-part (auto-split): `{"ok": true, "parts": 3, "url": "...", "urls": ["...", "...", "..."]}`

## Limits

- Content up to 64KB per page (auto-split into linked parts if exceeded)
- Pages cannot be deleted — only edited
- Supported HTML: a, aside, b, blockquote, br, code, em, figcaption, figure, h3, h4, hr, i, img, li, ol, p, pre, s, strong, u, ul
- `h1/h2` → `h3`, `h5/h6` → `h4`
- `<table>` auto-converted to monospace `<pre>` with box-drawing borders

## Token

Stored in `~/.claude/telegraph/token.txt`. Created automatically on first use. Can be set via `TELEGRAPH_ACCESS_TOKEN` env.
