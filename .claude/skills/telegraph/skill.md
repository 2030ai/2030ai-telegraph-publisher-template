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

Telegraph pages look best when clean and minimal. Avoid visual clutter:

- **One h3** at most for a section title. Use h4 sparingly for subsections only.
- **Minimal inline formatting** — don't stack bold + italic + code in one sentence.
- **Tables** render as monospace `<pre>` blocks with box-drawing borders — they look clean, use freely.
- **Short paragraphs** — 2-4 sentences each. Break up walls of text.
- Don't wrap entire paragraphs in bold or italic.
- Prefer lists over long comma-separated enumerations.

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
