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

## Quick start

```bash
# HTML
echo '<p>Content</p>' | python3 ~/.claude/telegraph/publish.py create --title "Title"

# Markdown
python3 ~/.claude/telegraph/publish.py create --title "Title" --format markdown --file notes.md

# Plain text
echo 'Just text' | python3 ~/.claude/telegraph/publish.py create --title "Title" --format text

# From file
python3 ~/.claude/telegraph/publish.py create --title "Title" --file path/to/file.html
```

## Commands

| Command | Description |
|---------|-------------|
| `create` | Create page. `--title` (required), `--format` (html/markdown/text), `--file` or stdin |
| `edit` | Edit page. `--path` (from URL), `--title`, `--file` or stdin |
| `get` | Page info. `--path`, `--return-content` |

## Output

JSON: `{"ok": true, "url": "https://telegra.ph/...", "path": "..."}`

## Workflow

When user asks to "publish to telegraph" or "share this as a link":
1. Generate content (HTML or Markdown)
2. Pipe to script via heredoc or `--file`
3. Return URL to user

## Limits

- Content up to 64KB (checked automatically)
- Pages cannot be deleted — only edited
- Supported HTML tags: a, aside, b, blockquote, br, code, em, figcaption, figure, h3, h4, hr, i, img, li, ol, p, pre, s, strong, u, ul
- `h1/h2` auto-mapped to `h3`, `h5/h6` to `h4`
- Tables (`table`) not supported by Telegraph — use screenshots or text

## Token

Stored in `~/.claude/telegraph/token.txt`. Created automatically on first use. Can be set via `TELEGRAPH_ACCESS_TOKEN` env.
