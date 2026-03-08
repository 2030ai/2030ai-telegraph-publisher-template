# Telegraph Publisher

Publish anything to [telegra.ph](https://telegra.ph) from the command line or [Claude Code](https://docs.anthropic.com/en/docs/claude-code). HTML, Markdown, plain text — pipe it in, get a link back.

**Zero dependencies.** Python 3.10+ stdlib only.

## Install

```bash
git clone https://github.com/2030ai/2030ai-telegraph-publisher-template.git
cd 2030ai-telegraph-publisher-template
chmod +x install.sh
./install.sh
```

This copies `publish.py` to `~/.claude/telegraph/` and the skill to `~/.claude/skills/telegraph/`.

### Manual install

```bash
mkdir -p ~/.claude/telegraph ~/.claude/skills/telegraph
cp publish.py ~/.claude/telegraph/publish.py
cp .claude/skills/telegraph/skill.md ~/.claude/skills/telegraph/skill.md
```

## Usage

### Create a page

```bash
# From HTML
echo '<h3>My Article</h3><p>Hello world!</p>' | python3 ~/.claude/telegraph/publish.py create --title "My Article"

# From Markdown
python3 ~/.claude/telegraph/publish.py create --title "Notes" --format markdown --file notes.md

# From plain text
echo 'Simple text content' | python3 ~/.claude/telegraph/publish.py create --title "Quick Note" --format text

# With heredoc (best for Claude Code)
python3 ~/.claude/telegraph/publish.py create --title "Analysis" --format markdown << 'EOF'
# Market Analysis

Key findings:
- **Growth**: 15% YoY
- **Risk**: moderate

> Data as of Q1 2026
EOF
```

Output:
```json
{"ok": true, "url": "https://telegra.ph/My-Article-03-08", "path": "My-Article-03-08"}
```

### Edit a page

```bash
echo '<p>Updated content</p>' | python3 ~/.claude/telegraph/publish.py edit --path "My-Article-03-08" --title "My Article v2"
```

### Get page info

```bash
python3 ~/.claude/telegraph/publish.py get --path "My-Article-03-08" --return-content
```

## Claude Code Integration

Once installed, the skill activates on triggers like:
- "publish to telegraph"
- "опубликуй на телеграф"
- "share this as a telegra.ph link"

Claude will automatically format your content and return a shareable link.

## Features

- **3 input formats**: HTML, Markdown, plain text
- **Pipe-friendly**: stdin or `--file`
- **Auto-account**: Telegraph account created on first use, token stored locally
- **HTML converter**: Maps HTML → Telegraph DOM nodes with smart fallbacks (h1→h3, div→passthrough, table→pre)
- **Markdown converter**: Full support for headers, bold, italic, links, code blocks, lists, blockquotes, strikethrough
- **Size check**: 64KB content limit validated before API call

## How it works

```
Content (HTML/MD/text)
  → Converter (html.parser / regex)
    → Telegraph Node array (JSON)
      → POST api.telegra.ph/createPage
        → https://telegra.ph/Your-Page
```

Telegraph API accepts [DOM-like nodes](https://telegra.ph/api#Node), not raw HTML. The script handles the conversion:

| Input tag | Telegraph output |
|-----------|-----------------|
| `h1`, `h2` | `h3` |
| `h5`, `h6` | `h4` |
| `div`, `span`, `section` | Pass-through (children preserved) |
| `table` | Skipped (use screenshots) |
| `b`, `i`, `a`, `code`, `pre`, `ul`, `ol`, `blockquote`, `img`, `hr` | Direct mapping |

## Token

Stored at `~/.claude/telegraph/token.txt`. Created automatically on first run.

Override with environment variable:
```bash
export TELEGRAPH_ACCESS_TOKEN=your_token_here
```

## Limits

- Title: 1-256 characters
- Content: up to 64KB (JSON-serialized nodes)
- Pages cannot be deleted, only edited
- No `<table>` support in Telegraph

## License

MIT
