# Telegraph Publisher — Agent Rules

## Project

CLI tool + Claude Code skill for publishing content to telegra.ph.
Single Python file (`publish.py`), stdlib only, zero external dependencies.

## Key files

- `publish.py` — main CLI script (HTML/Markdown/text → Telegraph nodes → API)
- `.claude/skills/telegraph/skill.md` — Claude Code skill with triggers and workflow
- `install.sh` — installs to `~/.claude/` for global availability

## Conventions

- No external dependencies — stdlib only (`urllib.request`, `html.parser`, `json`, `argparse`)
- JSON output on stdout, diagnostics on stderr
- Token auto-created on first use, stored in `~/.claude/telegraph/token.txt`
- Pipe-friendly: content via stdin or `--file`
- Format auto-detected from file extension (`.md` → markdown, `.html` → html, `.txt` → text)
- HTML `<table>` and Markdown pipe tables → monospace `<pre>` with box-drawing borders
- Content > 64KB auto-split into linked multi-part pages
- Image upload via `upload` command (Telegraph file hosting, no token required)
